import random
import numpy as np
import copy
from typing import List, Dict

class GeneticOptimizer:
    def __init__(self, population_size: int = 50, mutation_rate: float = 0.1, generations: int = 100):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations

    def fitness_function(self, path: List[Dict], fuel_level: float, passenger_count: int) -> float:
        """
        Calculate fitness based on fuel-passenger efficiency.
        """
        # Simplistic efficiency model: fitness = (passengers / fuel_consumed)
        # Fuel consumed is proportional to path distance
        distance = self._calculate_distance(path)
        if distance == 0:
            return 0

        # Penalize if fuel_level is low and distance is high
        fuel_consumption_rate = 0.5 + (passenger_count * 0.05)
        estimated_fuel_needed = distance * fuel_consumption_rate

        if estimated_fuel_needed > fuel_level:
            return -1.0 # Invalid path if fuel is insufficient

        efficiency = passenger_count / estimated_fuel_needed
        return efficiency

    def _calculate_distance(self, path: List[Dict]) -> float:
        distance = 0
        for i in range(len(path) - 1):
            p1 = path[i]
            p2 = path[i+1]
            distance += np.sqrt((p2['lat'] - p1['lat'])**2 + (p2['lon'] - p1['lon'])**2)
        return distance

    def crossover(self, parent1: List[Dict], parent2: List[Dict]) -> List[Dict]:
        if len(parent1) < 2: return parent1
        cp = random.randint(1, len(parent1) - 1)
        child = parent1[:cp] + parent2[cp:]
        return child

    def mutate(self, path: List[Dict]) -> List[Dict]:
        new_path = copy.deepcopy(path)
        for i in range(len(new_path)):
            if random.random() < self.mutation_rate:
                new_path[i]['lat'] += random.uniform(-0.001, 0.001)
                new_path[i]['lon'] += random.uniform(-0.001, 0.001)
        return new_path

    def optimize(self, initial_path: List[Dict], fuel_level: float, passenger_count: int) -> List[Dict]:
        population = [self.mutate(initial_path) for _ in range(self.population_size)]

        for _ in range(self.generations):
            # Evaluate
            scores = [(self.fitness_function(p, fuel_level, passenger_count), p) for p in population]
            # Filter out invalid paths
            scores = [s for s in scores if s[0] != -1.0]
            if not scores:
                return initial_path

            scores.sort(key=lambda x: x[0], reverse=True)

            # Selection
            best_half = [s[1] for s in scores[:self.population_size // 2]]

            # Evolve
            new_population = best_half.copy()
            while len(new_population) < self.population_size:
                p1, p2 = random.sample(best_half, 2)
                child = self.crossover(p1, p2)
                new_population.append(self.mutate(child))
            population = new_population

        return max(population, key=lambda p: self.fitness_function(p, fuel_level, passenger_count))
