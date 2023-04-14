import random as rand
import datetime
import heapq
from math import floor

facilitators = ["Lock",
                "Glen",
                "Banks",
                "Richards",
                "Shaw",
                "Singer",
                "Uther",
                "Tyler",
                "Numen",
                "Zeldin"]

room_capacities = {"Slater 003": 45,
                   "Roman 216":	30,
                   "Loft 206":	75,
                   "Roman 201":	50,
                   "Loft 310":	108,
                   "Beach 201":	60,
                   "Beach 301":	75,
                   "Logos 325":	450,
                   "Frank 119":	60}

times = [10, 11, 12, 13, 14, 15]

appendix = {
    "SLA100A": [50,
                ["Glen", "Lock", "Banks", "Zeldin"],
                ["Numen", "Richards"]],
    "SLA100B": [50,
                ["Glen", "Lock", "Banks", "Zeldin"],
                ["Numen", "Richards"]],
    "SLA191A": [50,
                ["Glen", "Lock", "Banks", "Zeldin"],
                ["Numen", "Richards"]],
    "SLA191B": [50,
                ["Glen", "Lock", "Banks", "Zeldin"],
                ["Numen", "Richards"]],
    "SLA201": [50,
               ["Glen", "Banks", "Zeldin", "Shaw"],
               ["Numen", "Richards", "Singer"]],
    "SLA291": [50,
               ["Lock", "Banks", "Zeldin", "Singer"],
               ["Numen", "Richards", "Shaw", "Tyler"]],
    "SLA303": [60,
               ["Glen", "Zeldin", "Banks"],
               ["Numen", "Singer", "Shaw"]],
    "SLA304": [25,
               ["Glen", "Banks", "Tyler"],
               ["Numen", "Singer", "Shaw", "Richards", "Uther", "Zeldin"]],
    "SLA394": [20,
               ["Tyler, Singer"],
               ["Richards", "Zeldin"]],
    "SLA449": [60,
               ["Tyler", "Singer", "Shaw"],
               ["Zeldin", "Uther"]],
    "SLA451": [100,
               ["Tyler", "Singer", "Shaw"],
               ["Zeldin", "Uther", "Richards", "Banks"]]
}

rooms = list(room_capacities.keys())
classes = ["SLA100A",
           "SLA100B",
           "SLA191A",
           "SLA191B",
           "SLA201",
           "SLA291",
           "SLA303",
           "SLA304",
           "SLA394",
           "SLA449",
           "SLA451"]


class Activity:
    def __init__(self, name, room, time, facilitator):
        self.name = name
        self.room = room
        self.time = time
        self.facilitator = facilitator

    def calc_fitness(self, schedule):
        fitness = 0
        appendix_entry = appendix[self.name]

        # same room check
        for activity in schedule.time_table[self.time]:
            if activity == self:
                continue
            else:
                if activity.room == self.room:
                    fitness += -0.5

        # room capacity check
        expected_enrollment = appendix_entry[0]
        room_capacity = room_capacities[self.room]
        if expected_enrollment < room_capacity:
            fitness += -0.5
        elif expected_enrollment > (6 * room_capacity):
            fitness += -0.4
        elif expected_enrollment > (3 * room_capacity):
            fitness += -0.2
        else:
            fitness += 0.3

        # preferred facilitator check
        preferred_facilitators = appendix_entry[1]
        other_facilitators = appendix_entry[2]

        if self.facilitator in preferred_facilitators:
            fitness += 0.5
        elif self.facilitator in other_facilitators:
            fitness += 0.2
        else:
            fitness += -0.1

        # facilitator specific checks
        concurrent_activities = 0
        for activity in schedule.time_table[self.time]:
            if activity != self:
                if self.facilitator == activity.facilitator:
                    concurrent_activities += 1

        if concurrent_activities == 0:
            fitness += 0.2
        elif concurrent_activities > 0:
            fitness += -0.2

        facilitator_class_amount = len(schedule.facilitator_classes[self.facilitator])
        if facilitator_class_amount > 4:
            fitness += -0.5
        elif facilitator_class_amount == 1 or facilitator_class_amount == 2:
            if self.facilitator != "Tyler":
                fitness += -0.4
        elif facilitator_class_amount > 2 and self.facilitator == "Tyler":
            fitness += -0.4

        # consecutive facilitator activity criteria
        for activity in schedule.time_table[self.time]:
            if activity != self and activity.facilitator == self.facilitator and activity.time == self.time:
                fitness += ActivityPair(self, activity).calc_consecutive_criteria()

        return fitness

    def activity_to_string(self):
        return "{} in {} at  {}: taught by {}".format(self.name, self.room, self.time, self.facilitator)


class ActivityPair:
    far_locations = ["Roman", "Beach"]

    def __init__(self, activity_a, activity_b):
        self.activity_a = activity_a
        self.activity_b = activity_b
        self.pair_fitness = 0

    def calc_time_difference(self):
        return abs(self.activity_a.time - self.activity_b.time)

    def calc_consecutive_criteria(self):
        score = 0
        time_difference = self.calc_time_difference()
        if time_difference == 1:
            score += 0.5

            if (self.activity_a.room in ActivityPair.far_locations) or\
                    (self.activity_b.room in ActivityPair.far_locations):
                if (self.activity_a.room not in ActivityPair.far_locations) or\
                        (self.activity_b.room not in ActivityPair.far_locations):
                    score += -0.4
        return score

    def calc_specific_time_criteria(self):
        score = 0
        time_difference = self.calc_time_difference()

        score += self.calc_consecutive_criteria()

        if time_difference == 2:
            score += 0.25
        elif time_difference == 0:
            score += -0.25

        return score


class Schedule:
    def __init__(self, activities, activity_pairs):
        self.time_table = {}  # time slot and classes during that time
        self.facilitator_classes = {}  # facilitator and their classes

        self.activities = activities
        self.activity_pairs = activity_pairs
        self.fitness = 0

        for activity in activities:
            time_table_item = self.time_table.get(activity.time) or []
            time_table_item.append(activity)
            self.time_table[activity.time] = time_table_item

            facilitator_item = self.facilitator_classes.get(activity.facilitator) or []
            facilitator_item.append(activity)
            self.facilitator_classes[activity.facilitator] = facilitator_item

    def calc_specific_fitness(self):
        fitness = 0

        sla100_pair = self.activity_pairs[0]
        sla191_pair = self.activity_pairs[1]

        sla100_time_difference = sla100_pair.calc_time_difference()
        sla191_time_difference = sla191_pair.calc_time_difference()

        if sla100_time_difference > 4:
            fitness += 0.5
        elif sla100_time_difference == 0:
            fitness -= 0.5

        if sla191_time_difference > 4:
            fitness += 0.5
        elif sla191_time_difference == 0:
            fitness -= 0.5

        section_combinations = [ActivityPair(sla100_pair.activity_a, sla191_pair.activity_a),
                                ActivityPair(sla100_pair.activity_a, sla191_pair.activity_b),
                                ActivityPair(sla100_pair.activity_b, sla191_pair.activity_a),
                                ActivityPair(sla100_pair.activity_b, sla191_pair.activity_b)]

        for activity_pair in section_combinations:
            fitness += activity_pair.calc_specific_time_criteria()

        return fitness

    def calc_schedule_fitness(self):
        fitness = 0
        self.fitness = 0

        for activity in self.activities:
            fitness += activity.calc_fitness(self)

        fitness += self.calc_specific_fitness()

        self.fitness = fitness
        return fitness

    def __lt__(self, other):
        return self.fitness < other.fitness

    def output_to_file(self):
        with open("best_schedule.txt", 'w') as file:
            for time in times:
                activities = self.time_table.get(time)
                if activities:
                    for activity in activities:
                        file.write(activity.activity_to_string() + "\n")

            #for activity in self.activities:
             #   file.write(activity.activity_to_string() + "\n")



def generate_random_activity(activity_name):
    rand_room = rooms[rand.randint(0, len(rooms) - 1)]
    rand_time = times[rand.randint(0, len(times) - 1)]
    rand_facilitator = facilitators[rand.randint(0, len(facilitators) - 1)]
    return Activity(activity_name, rand_room, rand_time, rand_facilitator)

def initialize_population(size):
    population = []
    total_fitness = 0

    for i in range(0, size):
        schedule_activities = []
        schedule_activity_pairs = []

        last_activity = None
        for j in range(0, len(classes)):
            activity_name = classes[j]
            new_activity = generate_random_activity(activity_name)

            if j == 0 or j == 2: # one of the pair activities
                last_activity = new_activity
            else:
                if last_activity:
                    schedule_activities.append(last_activity)
                    schedule_activities.append(new_activity)

                    activity_pair = ActivityPair(last_activity, new_activity)
                    schedule_activity_pairs.append(activity_pair)
                    last_activity = None
                else:
                    schedule_activities.append(new_activity)

        new_schedule = Schedule(schedule_activities, schedule_activity_pairs)
        new_schedule_fitness = new_schedule.calc_schedule_fitness()
        total_fitness += new_schedule_fitness
        heapq.heappush(population, (new_schedule_fitness, new_schedule))

    return population, total_fitness


def make_new_child(parent_a, parent_b, mutated=False):
    child_activities = parent_a.activities[0:5] + parent_b.activities[5:]
    child_pair_activities = [parent_a.activity_pairs[0], parent_a.activity_pairs[1]]

    if mutated:
        activity_index = rand.randint(0, len(child_activities) - 1)
        old_activity = child_activities[activity_index]
        child_activities[activity_index] = generate_random_activity(old_activity.name)

    return Schedule(child_activities, child_pair_activities)


def return_best_schedule(schedules):
    for i in range(0, len(schedules) - 1):
        heapq.heappop(schedules)
    return schedules[-1][1]


def iterative_selection(total_fitness):
    new_fitness = total_fitness
    for i in range(0, len(schedules)):
        removed_schedule = heapq.heappop(schedules)[1]
        new_fitness -= removed_schedule.fitness

        parent_a = schedules[rand.randint(0, len(schedules) - 1)][1]
        parent_b = schedules[rand.randint(0, len(schedules) - 1)][1]
        while parent_b == parent_a:  # ensure parents are different
            parent_b = schedules[rand.randint(0, len(schedules) - 1)][1]

        child = None
        if rand.random() < mutation_rate:
            child = make_new_child(parent_a, parent_b, True)
        else:
            child = make_new_child(parent_a, parent_b, False)

        child_fitness = child.calc_schedule_fitness()
        heapq.heappush(schedules, (child_fitness, child))
        new_fitness += child_fitness
    return new_fitness

def generational_selection(total_fitness):
    new_fitness = total_fitness
    for i in range(0, int(len(schedules) / 2)):  # remove 250 weakest
        removed_schedule = heapq.heappop(schedules)[1]
        new_fitness -= removed_schedule.fitness

    new_children = []
    for i in range(0, len(schedules)):
        parent_a = schedules[rand.randint(0, len(schedules) - 1)][1]
        parent_b = schedules[rand.randint(0, len(schedules) - 1)][1]
        while parent_b == parent_a:  # ensure parents are different
            parent_b = schedules[rand.randint(0, len(schedules) - 1)][1]

        child = None
        if rand.random() < mutation_rate:
            child = make_new_child(parent_a, parent_b, True)
        else:
            child = make_new_child(parent_a, parent_b, False)

        new_children.append(child)

    for child in new_children:
        child_fitness = child.calc_schedule_fitness()
        heapq.heappush(schedules, (child_fitness, child))
        new_fitness += child_fitness

    return new_fitness

if __name__ == '__main__':
    choice = None
    while choice not in ["x", "X"]:
        choice = input("1.Iterative selection\n2.Generational selection\n3. X to exit\n--> ")
        if choice in ["1", "2"]:
            if choice == "1":
                fitness_function = iterative_selection
            else:
                fitness_function = generational_selection

            schedules = []
            rand.seed(datetime.time())
            schedules, total_fitness = initialize_population(500)
            mutation_rate = 0.01

            generation = 0
            last_average_fitness = total_fitness / len(schedules)

            while True:  # generation
                generation += 1
                average_fitness = total_fitness / len(schedules)
                increase_percentage = (((average_fitness - last_average_fitness) / last_average_fitness) * 100)

                print("Generation:", generation, ":",
                      "Average fitness {:.5f}".format(average_fitness),
                      "Percentage Improvement: {:.5f}".format(increase_percentage))

                if generation >= 100:
                    if increase_percentage >= 0 and increase_percentage <= 1:
                        best_schedule = return_best_schedule(schedules)
                        print("Best fitness from generation", generation, ":", best_schedule.fitness)
                        best_schedule.output_to_file()
                        break

                # the mutation rate halving causes it to converge on a lower fitness too early...

                # if floor(average_fitness) - floor(last_average_fitness) >= 1:
                #     mutation_rate = mutation_rate / 2

                last_average_fitness = average_fitness

                total_fitness = fitness_function(total_fitness)
            else:
                print("Enter a valid choice")

