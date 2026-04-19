import pytest
from ..service.optimization import GeneticOptimizer

def test_genetic_optimization():
    optimizer = GeneticOptimizer(population_size=10, generations=5)
    initial_path = [
        {"lat": 0.0, "lon": 0.0},
        {"lat": 0.01, "lon": 0.01}
    ]
    fuel_level = 100.0
    passenger_count = 50

    optimized_path = optimizer.optimize(initial_path, fuel_level, passenger_count)

    assert len(optimized_path) == len(initial_path)
    assert isinstance(optimized_path, list)
    assert "lat" in optimized_path[0]

def test_fitness_function():
    optimizer = GeneticOptimizer()
    path = [{"lat": 0.0, "lon": 0.0}, {"lat": 0.01, "lon": 0.01}]

    fitness = optimizer.fitness_function(path, fuel_level=100, passenger_count=10)
    assert fitness > 0

    # Test insufficient fuel
    low_fuel_fitness = optimizer.fitness_function(path, fuel_level=0.00001, passenger_count=10)
    assert low_fuel_fitness == -1.0
