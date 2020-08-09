from __future__ import unicode_literals, print_function

import plac
import random
import warnings
from pathlib import Path
import spacy
from spacy.util import minibatch, compounding
import os
import operator
import functools

import pandas as pd
import torch
import numpy as np
from datetime import datetime
import numpy as np
import datetime
import matplotlib.pyplot as plt
from scipy.stats import normaltest
import random
import copy
import nltk
from nltk import word_tokenize
# import twint
import spacy
import en_core_web_sm
import geonamescache
from spacy import displacy
from geopy.geocoders import Nominatim
import re
from nltk.corpus import stopwords
import time

from spacy.tokens import Token
from spacy.matcher import Matcher, PhraseMatcher

#this class is used to extract the relevant information for countries mentioned in each report
#for context in terms of order return_sentences_for_countries -> country_short_list -> create_countries_cities_dict
class InformationExtractor():
    def __init__(self, nlp_model):
        self.gc = geonamescache.GeonamesCache() 
        self.all_countries = self.gc.get_countries_by_names()
        self.nlp = spacy.load(nlp_model)
        self.geolocator = Nominatim(user_agent="MenViz")
        #Global variable end_early is to ensure correct identification for AR's of each location
        self.end_early=False
        self.country_list = ['Benin', 'Burkina Faso', 'Burundi', 'Cameroun', 'Centrafrique', "Côte d'Ivoire", 'Ethiopia', 
                'Ghana', 'Guinea', 'Guinea Bissau', 'Gambia', 'Kenya', 'Mali', 'Mauritania', 'Niger', 'Nigeria', 
                'Congo', 'Senegal' , 'South Sudan', 'Sudan', 'Sierra Lone', 
                'Tanzania', 'Chad', 'Togo', 'Uganda']
        self.extensive_country_list = {0: ["Benin", "Bénin"], 1:["Burkina Faso", "Burkina"], 2: ["Burundi"], 3:["Cameroun", 
                          "Cameroon"], 4:["Centrafrique", "Central Africa", "Central African Republuc"], 
                         5: ["Côte d'Ivoire", "Ivory Coast"], 6:["Ethiopia"], 7: ["Ghana"], 8:["Guinea", "Guinée"], 9: 
                         ["Guinea Bissau", "Guinée Bissau"], 10:["Gambia"], 11:["Kenya"], 12: ["Mali"], 13: 
                          ["Mauritania", "Mauritanie"], 14: ["Niger"], 15: ["Nigeria"], 
                          16:["Democratic Republic of Congo", "Congo", "Dem. Rep. Congo"], 17:["Senegal", "Sénégal"], 
                          18:["South Sudan"], 19: ["Sudan"], 20: ["Sierra Lone"], 21: ["Tanzania"], 22: ["Chad", 
                         "Tchad", "Tchad"], 23: ["Togo"], 24: ["Uganda"]}
        #problematic cases to discard after obtaininig named entities
        self.problematic_cases = ["Upper", "Upper East", "Upper West", "East"]
                         
    #used to check a country and return its corresponding index - do this by looping through the values of the 
    #extensive dictionary list (specifically, loop through all the countries that begin with the same letter) 
    #to reduce computation
    #clean_first is a positional parameter that is used specifically when checking which country a city lies in
    #(i.e. using geopy's diplsay_name)
    def check_if_country(self, country, clean_first=False):
        if clean_first:
            if "Tchad" in country:
                country = "Chad"
        #Côte d'Ivoire will not get recognized for parsing reasons, so we check for it separately
        if "Côte" in country and "Ivoire" in country:
            return self.country_list.index("Côte d'Ivoire")
        #filter countries to only look at ones that start with the same letter
        same_letter_countries = list(filter(lambda x: x.startswith(country[0]), self.country_list))
        for cntry in same_letter_countries:
            if country in self.extensive_country_list[self.country_list.index(cntry)]:
                #return country index (corresponding to position in self.country_list)
                return self.country_list.index(self.extensive_country_list[self.country_list.index(cntry)][0])
        return -1
    #function that will extract the location tags from a given report and return a dictionary of countries as keys
    #and any corresponding cities mentioned as the values
    #note for consistency, the country keys will be represented as ints
    def country_short_list(self, sentences):
        #add a time delay since the geopy API has a low request limit
        time.sleep(0.000000001)
        #array with all cities/countries 
        locations = []
        #dictionary with keys = locations and values = length two array with 0th index start chr and 1st index = end
        chr_loc_segmentations = {}
        doc = self.nlp(sentences)
        #extract any ner tagged with locations and append them to a location array
        ents = [(e.text, e.start_char, e.end_char, e.label_) for e in doc.ents if e.label_ in ["GPE", "LOC", "FAC"]]
        for (txt, start_char, end_char, _) in ents:
            #remove brackets since this might be picked by the NER
            if ")" in txt:
                txt = txt.split(")")[0]
                print("DFDFDFD")
            #check problematic cases
            if txt in self.problematic_cases:
                continue
            locations.append(txt)
        #since some of the recognized entities are not recognized by the geocoder, need to put into a format that 
        #it can geocode
#         missing_loc = self.clean_up_cases(locations)
        #remove any duplicates from the list
        locations = list(dict.fromkeys(locations))
#         print(locations)
        countries_cities = self.create_countries_cities_dict(locations)
        return countries_cities
    
    def clean_up_loc(self, loc):
        
        if ";" in loc:
            index = loc.index(";")
            loc = loc[:index]
        if "of" in loc:
            words = loc.split()
            loc = words[-1]
            
        if "Tchad" in loc:
            loc = loc.split("/")[0].strip()
        
        if "Congo" in loc:
            loc = loc[-5:]
            belonging_to_country = self.country_list.index(str(loc))
        elif "Côte d'Ivoire" in loc:
            belonging_to_country = self.country_list.index("Côte d'Ivoire")
        else:
            belonging_to_country = self.country_list.index(str(loc).split(",")[-1].strip())
        return belonging_to_country
    
    #geocode can return an array of possible locations - this function will sift through the options
    #and return any relevant ones - possibile_cities is an array of locations returned from the geocoder and 
    #countries_cities is the dictionary that we will eventually return from this class
    #note since the geolocator may change the spelling of the location after localizing it, and we still need
    #to match the locations to numerical data in the report - we save the original string if the location is found
    def search_array_of_cities(self, possibile_cities, countries_cities, place):
        for city in possibile_cities:
            cntry_code = self.check_if_country(city.raw["display_name"].split(",")[-1].strip(), clean_first=True)
            if cntry_code != -1:
                #TODO: add code to extract the boundingbox values from the city.raw dictionary
                city_name = city.raw["display_name"].split(",")[0]
                if cntry_code not in countries_cities:
                    countries_cities[cntry_code] = [place]
                else:
                    #avoid accidental repetitions of the same location
                    if place not in countries_cities[cntry_code]:
                        countries_cities[cntry_code].append(place) 
                #found a match thus we don't need to search through the rest of the results
                break
    
    #as input takes array of countries/cities and returns a dictionary with countries as keys and cities as values
    def create_countries_cities_dict(self, locations):
        #dictionary with countries as keys and cities mentioned as values
        countries_cities = {}
        #need to look at all possible country options from the dictionary since geocoder will not be able to 
        #process it otherwise
        for place in locations:
            cntry_code = self.check_if_country(place)
            
            if cntry_code != -1:
                if cntry_code not in countries_cities:
                    #store the country as its corresponding int key from self.country_list array
                    countries_cities[cntry_code] = []
            elif place != None:
                loc = None
                try:
                    #the place must be a city thus we need to find which country this city is located in
                    locs = self.geolocator.geocode(place.strip(), exactly_one=False)
                    self.search_array_of_cities(locs, countries_cities, place)
                except Exception as e:
                    pass
        return countries_cities
    
    #return sentence containing specific substring from a report
    #will be used by passing in locations that are present (countries or cities) and returning the string associated 
    #with them - will
    def extract_sentence_given_substring(self, substring, report):
        return re.findall(r""+substring+"(?:[^\.]|\.(?=\d))*[\;).]", report)
        
    
    #given input a report, the function will computea dictionary with countries as keys and cities as values 
    #- this function will return a dictionary with countries as keys and an array of sentences that 
    #contain each of the country/city mentions in the report
    def return_sentences_for_countries(self, report):
        countries_data_dict = {}
        location_dict = self.country_short_list(report)
        for (country, cities) in location_dict.items():
            data_array = []
            #check if cities is empty
            if cities:
                for city in cities:
                    data_array.append((city, self.extract_sentence_given_substring(city, report)))
            else:
                data_array.append((country, self.extract_sentence_given_substring(self.country_list[country], report)))
            countries_data_dict[country] = data_array
        print(countries_data_dict)
        return countries_data_dict
    
    ###### CODE FROM HERE IS FOR EXTRACTING AR/CASES FROM CHOSEN SENTENCES
    
    def dynamically_find_ar(self, doc, start_chr, end_chr, location):
        #for sentences that contain multiple locations NOT separated by periods - need to check in a window ahead
        #if any new locations are being mentioned - we check ahead for any GPE tags
        look_ahead_entities = [e.label_ for e in doc[end_chr:end_chr+10].ents]
        if "GPE" in look_ahead_entities:
            self.end_early=True
        move_fwd = start_chr
        found = False
        #loop through until we either reach end of phrase or we find the atttack rate
        while not found and move_fwd < len(doc):
            move_fwd += 1
            try:
                if type(float(doc[move_fwd].text)) == float:
                    return doc[move_fwd]
            except Exception:
                pass
    
    def process_matches(self, string_id, start_chr, doc, location, end_chr):
        value = None
        if string_id == "cases":
            value = doc[start_chr - 1]
        elif string_id == "AR":
            value = self.dynamically_find_ar(doc, start_chr, end_chr, location, )
        elif string_id == "attack rate":
            value = doc[start_chr + 3]
        
        try:
            value = float(value.text)
        except Exception as e:
            return None
        return value 
    
    def set_up_matcher(self):
        matcher = Matcher(self.nlp.vocab)
        
        ar_patterns_v1 = [{"LOWER": "attack"}, {"LOWER": "rate"}]
        ar_patterns_v2 = [{"LOWER": "ar"}]

        cases_patterns_v1 = [{"TEXT": {"REGEX": "(case[s])"}}]
        
        matcher.add("AR", None, ar_patterns_v1)
        matcher.add("AR", None, ar_patterns_v2)
        matcher.add("cases", None, cases_patterns_v1)
        return matcher
    
    def find_match(self, matcher, sentence, city):
        
        doc = self.nlp(sentence)
        matches = matcher(doc)
        info = {}
        #due to output of regex statement, relevant location will be the first item in the doc
        #check second item to see if it's a number (e.g. in case of list of city, ar where keywords attack rate/cases
        #is not mentioned)
        try:
            if type(float(doc[1].text)) == float:
                info[city] = ('AR', float(doc[1].text))
        except Exception:
            for match_id, start, end in matches:
                location = city
                #check if city is a number => location is a country, and we need to parse it as such
                if type(city) == int:
                    location = self.country_list[city]
                #check we've matched with the noun representing the city
                string_id = self.nlp.vocab.strings[match_id]
                value = self.process_matches(string_id, start, doc, location, end)
                info[string_id] = value
                #Recall, we match with Regex - therefore LOC (location of interest) will always be at the start of the 
                #phrase, however there may be other locations in the same sentence if it was not cuttoff properly
                #e.g. due to missing punctuation marks etc. - if end_early is True, allows us to capture correct
                #metrics for each location and waste unnecessary computation
                if self.end_early:
                    self.end_early=False
                    break
        return info
    

    #function takes as a parameter a dictionary with keys as countries and values tuples containing (city, sentence)
    #return a dictionay with countries as keys and values as tuples containing (city, AR)
    def find_city_ars(self, countries_data_dict):
        matcher = self.set_up_matcher()
        #data dictionary contains countries as keys and values that are arrays of tuples (city, AR)
        data_dict = {}
        for (country, cities) in countries_data_dict.items():
            data_dict[country] = []
            for (city, sentence) in cities:
                if len(sentence) > 0:
                    determined_ar = self.find_match(matcher, sentence[0], city)
                    if determined_ar != None:
                        data_dict[country].append((city, determined_ar))
        print(data_dict)
        return data_dict


    #call this function to given a summary, give necessary info for the forecasting pipeline
    def symbolically_process_summary(self, summary):
        return self.find_city_ars(self.return_sentences_for_countries(summary))
    




