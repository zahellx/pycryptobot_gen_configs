from random import *
import os
import json
import re
import numpy as np
import time
import random
from multiprocessing import Pool
import sys

class DNA:
    def __init__(self, mutation_rate, n_individuals, n_selection, n_generations, base_currency, verbose = True):
        self.mutation_rate = mutation_rate
        self.n_individuals = n_individuals
        self.n_selection = n_selection
        self.n_generations = n_generations
        self.verbose = verbose
        self.base_currency = base_currency
        self.best_score = (0, [])
        self.population_best = (0, [])
        self.positions = {
            "disablebuynearhigh": 0,
            "buynearhighpcnt": 1,
            "nosellminpcnt": 2,
            "nosellmaxpcnt": 3,
            "sellatloss": 4,
            "selllowerpcnt": 5,
            "sellupperpcnt": 6,
            "trailingstoploss": 7,
            "trailingstoplosstrigger": 8,
            "sellatresistance": 9,
            "disablebullonly": 10,
            "disablebuymacd": 11,
            "disablebuyema": 12,
            "disablebuyobv": 13,
            "disablebuyelderray": 14,
            "disablefailsafefibonaccilow": 15,
            "disablefailsafelowerpcnt": 16,
            "disableprofitbankupperpcnt": 17,
            "disableprofitbankfibonaccihigh": 18,
            "disableprofitbankreversal": 19,
        }

    def create_individual(self):
        # TODO mejora, esto que se ponga tambien en la posicion con el indice, asi tenemos menos oportunidades de fallos
        # -- sellatloss --
        disablebuynearhigh = randint(0, 1) #0
        buynearhighpcnt = randint(1, 10) # if disablebuynearhigh else 0 #1
        # ----
        nosellminpcnt = randint(-30, -1) #2
        nosellmaxpcnt = randint(1, 30) #3
        # -- sellatloss -- Dependen del valor de sellatloss
        sellatloss = randint(0, 1) # 4
        selllowerpcnt = randint(-11, -1) # if sellatloss else 0 #5
        sellupperpcnt = randint(1, 10) # if sellatloss else 0 #6 
        # trailingstoploss = round(random.uniform(-5, -1), 1) # if sellatloss else 0 #7
        trailingstoploss = round(random.uniform(0.1, 5), 1) # if sellatloss else 0 #7
        trailingstoplosstrigger = randint(nosellmaxpcnt, 30) # if sellatloss else 0 #8
        # ----
        sellatresistance = randint(0, 1) # 9
        disablebullonly = randint(0, 1) # 10
        disablebuymacd = randint(0, 1) # 11
        disablebuyema = randint(0, 1) # 12
        disablebuyobv = randint(0, 1) #13
        disablebuyelderray =randint(0, 1) #14
        disablefailsafefibonaccilow = randint(0, 1) #15
        disablefailsafelowerpcnt = randint(0, 1) #16
        disableprofitbankupperpcnt = randint(0, 1) #17
        disableprofitbankfibonaccihigh = randint(0, 1) #18
        disableprofitbankreversal = randint(0, 1) #19
        
 
        return [disablebuynearhigh, buynearhighpcnt, nosellminpcnt, nosellmaxpcnt, sellatloss, selllowerpcnt, 
        sellupperpcnt, trailingstoploss, trailingstoplosstrigger, sellatresistance, disablebullonly, disablebuymacd,
        disablebuyema, disablebuyobv, disablebuyelderray, disablefailsafefibonaccilow, disablefailsafelowerpcnt, 
        disableprofitbankupperpcnt, disableprofitbankfibonaccihigh, disableprofitbankreversal]

    def create_population(self):
        return [self.create_individual() for _ in range(self.n_individuals)]
        
    def fitness_pruebas(self, individual):
        self.create_config(individual, 'config.json')
        os.system('docker-compose up -d')
        while(1):
            time.sleep(10)
            try:
                if os.system('docker container wait etheur') == 0:
                    break
            except:
                break

    def fitness(self, individual):
        service = str(randint(0, 100000000))
        docker_file = f"docker-compose-{service}.yaml"
        log_file = f"pycryptobot_{service}.log"
        config_file = f"config_{service}.json"
        with open(f'./market/GEN/{log_file}', 'w') as fp:
            pass
        with open(f'./market/GEN/{config_file}', 'w') as fp:
            pass

        self.create_config(individual, f'./market/GEN/{config_file}')

        # Read in the file
        with open('docker-compose-gen.yaml', 'r') as file :
            filedata = file.read()
        # Replace the target string
        filedata = filedata.replace('$SERVICE', service)
        filedata = filedata.replace('$CONTAINER_NAME', f'"{service}"')
        # Write the file out again
        with open(docker_file, 'w') as file:
            file.write(filedata)

        os.system(f'docker run -d --rm --name {service} -v $(pwd)/market/GEN/config_{service}.json:/app/config.json -v $(pwd)/market/GEN/pycryptobot_{service}.log:/app/pycryptobot.log -v $(pwd)/market/GEN/graphs:/app/graphs -v /etc/localtime:/etc/localtime:ro bot')
        while(1):
            time.sleep(10)
            try:
                res = os.system(f'docker container wait {service}')
                if res == 0 or 'No such container' in res:
                    break
            except:
                break

        with open(f'./market/GEN/{log_file}', 'r') as f:
            lines = f.read().splitlines()
            last_line = lines[-21:]
        fitness_match = re.search('.*All Trades Profit/Loss \\(EUR\\): (.*) \\(.*\\).*', str(last_line), re.IGNORECASE)
        
        os.remove(f'./market/GEN/{log_file}')
        os.remove(f'./{docker_file}')
        os.remove(f'./market/GEN/{config_file}')
        # os.system('docker rm -v $(docker ps -a -q -f status=exited) -y')
        # os.system('docker image prune -y')
        if fitness_match:
            return (int(float(fitness_match.group(1).replace("'", ""))), individual)
        else:
            return (0, individual)

    def selection(self, population):
        scores = []
        with Pool(processes=5) as pool:
            scores = pool.map(self.fitness, population)

        # scores = [(self.fitness(i), i) for i in population]
        order_scores = sorted(scores, reverse=True)
        if self.best_score[0] < order_scores[0][0]:
            self.best_score = order_scores[0]
        self.population_best = order_scores[0]
        sort_population = [i[1] for i in order_scores]
        return sort_population[:len(sort_population)-(len(sort_population)-self.n_selection)]

    def reproduction(self, population, selected):

        point = 0
        father = []

        for i in range(len(population)):
            point = np.random.randint(1, len(population[0]) - 1)
            father = random.sample(selected, 2)

            population[i][:point] = father[0][:point]
            population[i][point:] = father[1][point:]
        
        return population

    def mutation(self, population):
        for i in range(len(population)):
            if random.random() <= self.mutation_rate:
                point = np.random.randint(len(population[0]))
                new_value = self.mutate_ind(population[i], point)

                while new_value == population[i][point]:
                    self.mutate_ind(population[i], point)
                
                population[i][point] = new_value
            return population

    def mutate_ind(self, individual, point):
        if point in [0, 4, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]:
            new_value = 0 if individual[point] == 1 else 1
            # new_value = randint(0, 1)
        elif point in [1, 6]:
            new_value = randint(1, 10)
        elif point in [2]:
            new_value = randint(-30, -1)
        elif point in [4, 8]:
            new_value = randint(0, 30)
        elif point in [5]:
            new_value = randint(-11, -1)
        elif point in [7]:
            new_value = round(random.uniform(0.1, 5), 1)
        elif point in [4, 3]:
            new_value = randint(1, 30)
        else:
            raise Exception(f'Mutate no contempla la posicion {point}')
        return new_value

    def create_config(self, individual, config_file_path):
        with open('./market/template/config.json') as json_config:
            config = json.load(json_config)
            config['base_currency'] = self.base_currency
            # por si acaso, para cada elemento de posicion, cambiamos en la configuracion el valor de la key, por el que tendriamos en el individuo
            for element in self.positions.keys():
                config[element] = individual[self.positions[element]]
        with open(config_file_path, 'w') as outfile:
            json.dump(config, outfile)
    
    def run_geneticalgo(self):
        population = self.create_population()

        for i in range(self.n_generations):

            if self.verbose:
                print('___________')
                print('Generacion: ', i)
                print('Poblacion', population)
                print()

            selected = self.selection(population)
            population = self.reproduction(population, selected)
            population = self.mutation(population)
        print('___________')
        print(f'Best result: {self.best_score}')
        print(f'Best of population: {self.population_best}')
        print('___________')
        try:
            base_path = f"./market/{self.base_currency}"
            if not os.path.exists(base_path):
                os.makedirs(base_path)
            self.create_config(self.best_score[1], f'{base_path}/best_score_{self.base_currency}.json')
            with open(f'{base_path}/best_score_{self.base_currency}.txt', 'w') as f:
                f.write(f'Money: {self.best_score[0]}')
            self.create_config(self.population_best[1], f'{base_path}/population_best_{self.base_currency}.json')
            with open(f'{base_path}/population_best_{self.base_currency}.txt', 'w') as f:
                f.write(f'Money: {self.population_best[0]}')
        except:
            pass

    def run_geneticalgo_time(self):
        individual = self.create_individual()
        f = self.fitness_pruebas(individual)
        

def main():
    base_currency = sys.argv[1]
    os.system(f'docker build . -t bot -f ../Dockerfile')
    start_time = time.time()
    model = DNA(
        mutation_rate = 0.3,
        n_individuals = 10,
        n_selection = 5,
        n_generations = 10,
        base_currency = base_currency,
        verbose=True
        )
    model.run_geneticalgo()

    # model.run_geneticalgo_time()
    print("--- %s seconds ---" % (time.time() - start_time))

    
if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))