#!/usr/bin/env python
# coding: utf-8

import csv
import heapq
import math

# Overall time complexity O(n)
# use of a heap to maintain order only uses O(log n) for insertion
# Processing every player requires O(n)
# 
# Processing allows for O(1) calculations on restrictions of player placement
# Pools will not allow a player to be placed into a club if the calculated
# maximum amount from that player's club has been reached
# exception : those with no club


def pool_Maker(file_In):
    param_List = ["last", "first", "club", "rank", "year"]
    type_List = [str, str, str, str, int]
    pool_Sizes = [[6, 7],
                  [7, 8],
                  [5, 6]]
    max_Club_Count = {}

    # Player Class
    # Holds data regarding each player
    # - last name, first name, club name, rank letter, and year
    #
    # custom comparator function for use in storing players in a heap

    class Player:
        def __init__(self, params):

            self.last = params[0]
            self.first = params[1]
            self.club = params[2]
            self.rank = params[3][0]
            
            if self.rank != 'U':
                self.year = (int)(params[3][1:])
            else:
                self.year = None
        def __cmp__(self, other):
            if self.rank == other.rank:
                if self.year is not None and other.year is not None:
                    return self.year - other.year
                elif self.year is None:
                    return -1
                else:
                    return 1
            return ord(self.rank) - ord(other.rank)

    # Pool Class
    # Holds list of players contained in the pool
    #
    # id - pool id
    # player_List - list of players contained in pool
    # size - maximum size of pool
    # freq - dictionary of clubs and how many members of that club are in the current pool
    #
    # add_member - attempts to add a player to a pool, returns True on success, False on failure

    class Pool:
        id_num = 0

        def __init__(self, size):
            self.id = Pool.id_num
            Pool.id_num += 1
            self.player_List = []
            #self.average_Rank = ''
            self.size = size
            self.freq = {}
            
        def count_Clubs(self):
            self.freq = {}
            for member in self.player_List:
                if member.club in self.freq:
                    self.freq[member.club] += 1
                else:
                    self.freq[member.club] = 1
                
        def add_Player(self, p_in):
            # if pool size reached, return False
            if len(self.player_List) >= self.size:
                #print("Pool Max capacity reached")
                return False
            # if maximum club frequency reached, return False
            if p_in.club in self.freq and p_in.club in max_Club_Count:
                if self.freq[p_in.club] >= max_Club_Count[p_in.club] and p_in.club != '':
                    #print("Maximum number from club : " + p_in.club)
                    return False
            # if input object of correct type, add to pool / player list    
            if isinstance(p_in, Player):
                self.player_List.append(p_in)
                
                if p_in.club in self.freq:
                    self.freq[p_in.club] += 1
                else:
                    self.freq[p_in.club] = 1
                
                return True
            else:
                raise Exception('Invalid Object, Not of Type player')

    # Verify Type function
    # Verifies whether a given row from the CSV file matches the format
    # specified in type_List
    # - last name, first name, club name, rank letter, and year

    def verify_Type(row):
        for ind in range(len(row)):
            if not isinstance(row[ind], type_List[ind]):
                return False
        return True

    # Read CSV function
    # opens a given file to read in all information regarding players
    # returns a list of players and a dictionary of frequency counts for each club
    # - last name, first name, club name, rank letter, and year

    # NOTE : using a heap to store input players based on rank
    # heap maintains order of highest ranked player
    # heap insert is O(log n)
    # heap pop is O(1)
    # thus using a heap is faster than sorting a list of players

    def read_Csv(file_Name):
        all_Players = []
        club_Count = {}
        if not isinstance(file_Name, str):
            raise Exception('File name is of incorrect type')
        with open(file_Name) as csv_File:
            csv_Reader = csv.reader(csv_File, delimiter = ',')
            line_count = 0
            player_count = 0
            for row in csv_Reader:
                row  = [entry.strip() for entry in row]
                if verify_Type(row):
                    heapq.heappush(all_Players, Player(row))
                    if row[2] in club_Count:
                        club_Count[row[2]] += 1
                    else:
                        club_Count[row[2]] = 1
                    player_count += 1
                else:
                    print("Line # " + line_count + " does not match format")
                line_count += 1
        print('Completed Processing of ' + file_Name + '.')
        print(' Line Count: ', line_count, ', Player Count: ', player_count)
        return all_Players, club_Count

    # Classify Pool function
    # given a number of players, classify which pool sizes will work
    # returns a list of pool sizes
    #
    # is divisible - function tests if num players is fully divisible by a combination of the two numbers given

    def classify_Pool(num):
        def is_divisible (num, min, max):
            return num % min == 0 or num % max or (num % min) % max == 0
        for pair in pool_Sizes:
            if is_divisible(num, pair[0], pair[1]):
                return pair
        raise Exception('All Pool Size pairs are incompatible')

    # Alloc Pool function
    # given the number of players and the pool sizes
    # returns a list of pools that have the proper sizing

    def alloc_Pools( num_Players, pool_Size):
        
        all_Pools = []
        num_max_size = 0
        num_min_size = 0
        
        if num_Players % pool_Size[0] == 0:
            num_min_size = num_Players / pool_Size[0]
        elif num_Players % pool_Size[1] == 0:
            num_max_size = num_Players / pool_Size[1]
        else:
            num_max_size =  num_Players / pool_Size[1]
            num_min_size =  (num_Players % pool_Size[1]) / pool_Size[0]

        for i in range(num_min_size):
            all_Pools.append(Pool(pool_Size[0]))
        for i in range(num_max_size):
            all_Pools.append(Pool(pool_Size[1]))
            
        return all_Pools

    # Fill Pool function
    # given allocated pools and the heap of all players
    # return a list of pools filled using the players

    def fill_Pools(all_Pools, all_Players):
        # Variables for use in ensuring the serpentine allocation of players
        pool_Range = range(len(all_Pools))
        step = 1
        index = 0
        turn_around = False
        
        # Note: need to be careful that filled pools that are smaller than their peers
        # do not mess up order
        size_reached_flag = False
        
        while(len(all_Players) > 0):
            # Pull a player from the heap and start attempting to place in a pool
            temp_Player = heapq.heappop(all_Players)
            is_temp_Allocated = False
            num_Tries = 0
            
            # Attempt to place while number of tries does not exceed number of pools
            while num_Tries < len(all_Pools) and not is_temp_Allocated:
                if all_Pools[index].add_Player(temp_Player):
                    is_temp_Allocated = True
                
                turn_around = False
                # if hit edge either first or last pool
                # redo the edge and switch direction for serpentine allocation
                if (index == 0 and step == -1) or (index == len(all_Pools) - 1 and step == 1):
                        step = -step
                        turn_around = True
                if not turn_around:
                    index += step
                    num_Tries += 1
                
                if num_Tries == len(all_Pools):
                    size_reached_flag = True
                    
        for group in all_Pools:
            group.count_Clubs()
        return all_Pools

    # Driver portion
    # get player heap and club counts
    (pl, cl_ct) = read_Csv(file_In)

    # get appropriate pool sizes
    p_size = classify_Pool(len(pl))

    # allocate pools
    pools = alloc_Pools(len(pl), p_size)

    # get the maximum number of participants from the same club for any pool to have
    pool_div = len(pools) * 1.0
    cl_ct.update((k, math.ceil(v / pool_div )) for k, v in cl_ct.items())
    max_Club_Count = cl_ct

    # fill pools
    comp_pools = fill_Pools(pools, pl)

    # print pools
    for p in comp_pools:
        print("--)------- Pool # " + str(p.id + 1) +" -------(-- (" + str(len(p.player_List)) + ")")
        for play in p.player_List:
            print("{: <22} {: <22} {: <22} {: <22} {: <22}".format(play.first, play.last, play.club, play.rank, play.year))
        print(p.freq)


def main():
    print("Enter 1 to test custom file")
    opt = raw_input("Enter 2 to test preset list of files :")
    if int(opt) == 1:
        f = raw_input("Enter file name :")
        pool_Maker(f)
    elif int(opt) == 2:
        file_List = ["MEconflicts.csv", "MEentries.csv", "MEshort.csv"]
        for f in file_List:
            print("File : " + f)
            pool_Maker(f)

if __name__ == "__main__":
    main()