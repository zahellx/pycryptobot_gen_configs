from random import *
import os
import json
import re
import numpy as np
import time
import random
from multiprocessing import Pool

class DNA:
    def __init__(self, mutation_rate, n_individuals, n_selection, n_generations, verbose = True):
        self.mutation_rate = mutation_rate
        self.n_individuals = n_individuals
        self.n_selection = n_selection
        self.n_generations = n_generations
        self.verbose = verbose
        self.best_score = (0, [])
        self.population_best = (0, [])

    def create_individual(self):
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
        trailingstoploss = randint(-11, -1) # if sellatloss else 0 #7
        trailingstoplosstrigger = randint(1, 30) # if sellatloss else 0 #8
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
        # os.system('docker container wait etheur')

        while(1):
            time.sleep(10)
            try:
                if os.system('docker container wait etheur') == 0:
                    break
            except:
                break

        # with open('./market/GEN/pycryptobot.log', 'r') as f:
        #     lines = f.read().splitlines()
        #     last_line = lines[-21:]
        # fitness_match = re.search('.*All Trades Profit/Loss \\(EUR\\): (.*) \\(.*\\).*', str(last_line), re.IGNORECASE)
    
        # if fitness_match:
        #     print(int(float(fitness_match.group(1).replace("'", ""))))
        #     return int(float(fitness_match.group(1).replace("'", "")))
        # else:
        #     return 0

    def fitness(self, individual):
        service = str(randint(0, 100000000))
        docker_file = f"docker-compose-{service}.yaml"
        log_file = f"pycryptobot_{service}.log"
        config_file = f"config_{service}.json"
        with open(f'./market/GEN/{log_file}', 'w') as fp:
            pass
        with open(f'./market/GEN/{config_file}', 'w') as fp:
            pass

        self.create_config(individual, config_file)

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
        # os.system(f'docker-compose -f {docker_file} up -d')
        # os.system(f'docker container wait {service}')
        # os.system(f'docker-compose -f {docker_file} up --no-deps --remove-orphans')
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
        if point in [0,4 , 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]:
            new_value = 0 if individual[point] == 1 else 1
            # new_value = randint(0, 1)
        elif point in [1, 6]:
            new_value = randint(1, 10)
        elif point in [2]:
            new_value = randint(-30, -1)
        elif point in [4, 8]:
            new_value = randint(0, 30)
        elif point in [5, 7]:
            new_value = randint(-11, -1)
        elif point in [4, 3]:
            new_value = randint(1, 30)
        else:
            raise Exception('Mutate no contempla todas las posiciones')
        return new_value

    def create_config(self, individual, config_file):
        config = {
                "binance": {
                    "api_url": "https://api.binance.com",
                    "config": {
                        "base_currency": "DOT",
                        "quote_currency": "EUR",
                        "autorestart": 1,
                        "live": 0,
                        "disablebuynearhigh": individual[0],
                        "buynearhighpcnt": individual[1],
                        "nosellminpcnt": individual[2],
                        "nosellmaxpcnt": individual[3],
                        "sellatloss": individual[4],
                        "selllowerpcnt": individual[5],
                        "sellupperpcnt": individual[6],
                        "trailingstoploss": individual[7],
                        "trailingstoplosstrigger": individual[8],
                        "sellatresistance": individual[9],
                        "disablebullonly": individual[10],
                        "disablebuymacd": individual[11],
                        "disablebuyema": individual[12],
                        "disablebuyobv": individual[13],
                        "disablebuyelderray": individual[14],
                        "disablefailsafefibonaccilow": individual[15],
                        "disablefailsafelowerpcnt": individual[16],
                        "disableprofitbankupperpcnt": individual[17],
                        "disableprofitbankfibonaccihigh": individual[18],
                        "disableprofitbankreversal": individual[19],
                        "graphs": 0,
                        "verbose": 0,
                        "stats": 0,
                        "disablelog": 0,
                        "sim": "fast-sample",
                        "simstartdate": "2021-06-01",
                        "simenddate": "now"
                    }
                }
            }
        with open(f'./market/GEN/{config_file}', 'w') as outfile:
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
            self.create_config(self.best_score[1], f'best_score_{self.best_score[1].get("config").get("base_currency")}.json')
        except:
            pass

        try:
            self.create_config(self.population_best[1], f'population_best_{self.best_score[1].get("config").get("base_currency")}.json')
        except:
            pass

    def run_geneticalgo_time(self):
        individual = self.create_individual()
        f = self.fitness_pruebas(individual)
        



def main():
    os.system(f'docker build -t bot .')
    start_time = time.time()
    model = DNA(
        mutation_rate = 0.3,
        n_individuals = 10,
        n_selection = 5,
        n_generations = 10,
        verbose=True)
    model.run_geneticalgo()

    # model.run_geneticalgo_time()
    print("--- %s seconds ---" % (time.time() - start_time))

    
if __name__ == '__main__':
    start_time = time.time()
    main()
    print("--- %s seconds ---" % (time.time() - start_time))