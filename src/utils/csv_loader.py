import csv
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Car


async def load_cars_from_csv(csv_path: str, db: AsyncSession) -> int:
    """Carga autos desde CSV a la base de datos"""
    cars_created = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                # Verificar si el auto ya existe
                from sqlalchemy import select
                result = await db.execute(
                    select(Car).where(Car.stock_id == row['stock_id'])
                )
                existing = result.scalar_one_or_none()

                if existing:
                    continue  # Skip si ya existe

                # Crear nuevo auto
                car = Car(
                    stock_id=row['stock_id'],
                    km=int(row['km']),
                    price=Decimal(str(row['price'])),
                    make=row['make'],
                    model=row['model'],
                    year=int(row['year']),
                    version=row.get('version') or None,
                    bluetooth=row.get('bluetooth', '').lower() == 'sí',
                    length=Decimal(str(row['largo'])) if row.get('largo') else None,
                    width=Decimal(str(row['ancho'])) if row.get('ancho') else None,
                    height=Decimal(str(row['altura'])) if row.get('altura') else None,
                    car_play=row.get('car_play', '').lower() == 'sí',
                )

                db.add(car)
                cars_created += 1

                # Commit en batches de 100
                if cars_created % 100 == 0:
                    await db.commit()

            except Exception as e:
                print(f"Error procesando fila {row.get('stock_id', 'unknown')}: {e}")
                continue

        # Commit final
        await db.commit()

    return cars_created
