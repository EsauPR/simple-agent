"""Sample data for tests"""
from decimal import Decimal


def get_sample_car_data(stock_id: str = "TEST001", **kwargs):
    """Get sample car data"""
    defaults = {
        "stock_id": stock_id,
        "km": 50000,
        "price": Decimal("200000.00"),
        "make": "Toyota",
        "model": "Corolla",
        "year": 2020,
        "version": "XEI",
        "bluetooth": True,
        "car_play": False,
        "length": Decimal("4.63"),
        "width": Decimal("1.78"),
        "height": Decimal("1.45"),
    }
    defaults.update(kwargs)
    return defaults


def get_sample_cars_data(count: int = 3):
    """Get multiple sample cars data"""
    makes = ["Toyota", "Honda", "Nissan", "Volkswagen", "Mazda"]
    models = ["Corolla", "Civic", "Sentra", "Jetta", "Mazda3"]

    cars = []
    for i in range(count):
        cars.append(get_sample_car_data(
            stock_id=f"TEST{i+1:03d}",
            make=makes[i % len(makes)],
            model=models[i % len(models)],
            year=2020 + (i % 3),
            price=Decimal(f"{150000 + i * 50000}.00"),
            km=30000 + i * 10000,
        ))
    return cars


def get_sample_embedding(dimension: int = 1536):
    """Get sample embedding vector"""
    return [0.1 * (i % 10) for i in range(dimension)]


def get_sample_embeddings(count: int = 3, dimension: int = 1536):
    """Get multiple sample embeddings"""
    return [get_sample_embedding(dimension) for _ in range(count)]


def get_sample_knowledge_base_data(**kwargs):
    """Get sample knowledge base data"""
    defaults = {
        "content": "Kavak es una empresa líder en compra y venta de autos seminuevos en México.",
        "source_url": "https://www.kavak.com/mx",
        "embedding": get_sample_embedding(),
        "metadata_json": {"source": "website", "chunk_index": 0},
    }
    defaults.update(kwargs)
    return defaults
