#[IMPORTS]

import re
import os 
import json
import shutil
from os import getenv
from os import listdir
from io import BytesIO
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
import itertools
from itertools import chain
import unicodedata
#from decouple import config

import spacy
nlp = spacy.load("pt_core_news_sm")
from spacy.language import Language
from spacy_langdetect import LanguageDetector
from langdetect import detect

from transformers import AutoModelForTokenClassification, AutoTokenizer
import torch

from text_analysis import *
from log import Log
import warnings
warnings.filterwarnings("ignore")


# NER from hugging face
model_name = "pierreguillou/ner-bert-large-cased-pt-lenerbr"
model = AutoModelForTokenClassification.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)


logger = Log('speaker_assignment',__name__)


list_entities_not_consider = {'entities':['Covid', 'Covid-19', 'COVID', 
                                            'COVID-19','Deus','Não', 'não','.','&']}


current_dir = os.getcwd()
NAMES_AUX = pd.read_json(os.path.join(current_dir,'support_files', 'names.json'))


@logger.critical
def get_quotes_and_speakers(speaker_assignment):
    quotes_and_speakers = []
    for assignment in speaker_assignment:        
        if "undefined" in  assignment["entity_final"]:
            quotes_and_speakers.append({"quote" : assignment["quote_text"], "speaker" : assignment["entity_final"], "gender" : "undefined"})
        else:
            quotes_and_speakers.append({"quote" : assignment["quote_text"], "speaker" : assignment["entity_final"], "gender" : assignment["gender"]})
    return quotes_and_speakers

@logger.critical
def get_unique_speakers(speaker_assignment):
    unique_speakers = []
    for assignment in speaker_assignment:
        if "undefined" not in assignment["entity_final"]:
            speaker = {"speaker" : assignment["entity_final"], "gender" : assignment["gender"]}
            if speaker not in unique_speakers:
                unique_speakers.append(speaker)
    return unique_speakers


@logger.critical
def get_statistics(quotes_and_speakers, unique_speakers):
    statistics = {}
    statistics["total_quotes"] = len(quotes_and_speakers)
    statistics["total_defined_speakers"] = sum([1 if "undefined" not in assignment["speaker"] else 0 for assignment in quotes_and_speakers])
    statistics["total_undefined_speakers"] = statistics["total_quotes"] - statistics["total_defined_speakers"]
    statistics["female_speakers"] = sum([1 if assignment["gender"] == "F" else 0 for assignment in quotes_and_speakers])
    statistics["male_speakers"] = sum([1 if assignment["gender"] == "M" else 0 for assignment in quotes_and_speakers])
    statistics["undefined_gender_speakers"] = sum([1 if "undefined" in assignment["gender"] else 0 for assignment in quotes_and_speakers])
    statistics["unique_defined_speakers"] = len(unique_speakers)
    statistics["unique_female_speakers"] = sum([1 if assignment["gender"] == "F" else 0 for assignment in unique_speakers])
    statistics["unique_male_speakers"] = sum([1 if assignment["gender"] == "M" else 0 for assignment in unique_speakers])
    statistics["unique_undefined_gender_speakers"] = sum([1 if "undefined" in assignment["gender"] else 0 for assignment in quotes_and_speakers])
    



    return statistics    


@logger.critical
def identify_speakers(text, id_text):    
    logger.info('## --------------------------------------------- ##')
    logger.info('## --------------------------------------------- ##')
    logger.info('Start Identify speakers | text: %s' % id_text) 


    K = 3
    NUM_VERB_MIN = 1
    LENGTH_QUOTE_MIN = 4
    QUOTE_LANGUAGE = 'pt'

    # Paragraphs tokenization (a list), remove undesired HTML tags, remove ´, if any
    paragraphs_orig = [t.replace('\u200b', '').replace('´', '').replace('\n', '') for t in text.split('    ')]
    paragraphs = paragraphs_orig 
    
    
    # Remove empty entries, if any
    paragraphs[:] = [x for x in paragraphs if x]
	
    	
    ###################################
    ## -- QUOTE, ENTITIES, POSTAG -- ##
    ###################################

    # Apply 'apply_nlpmodels'
    try:
        # Apply NLP models to recognize entities and to POS tag text words
        ls_dfent_dfpos = apply_nlpmodels(paragraphs, nlp, list_entities_not_consider['entities'])  
        ls_postag = ls_dfent_dfpos[1]

        # Text with POSTAG labels
        df_postag = ls_postag_as_dataframe(ls_postag)
        nlp_worked = 1

    except (Exception) as e:
        #save_log(PATH_DATA + '/'  + "LOG/", "NLP", ARTICLEID)
        logger.warning('ERROR_NLP_%s: %s' % (id_text,e))
        nlp_worked = 0    
        return 111111


    if nlp_worked == 1:    

        # Apply 'quotes_dataframe'
        try:
            df_quotes_beg_end = quotes_dataframe(df_postag)
            quotes_worked = 1
        except (Exception) as e:
            #save_log(PATH_DATA + '/'  + "LOG/", "QUOTES", ARTICLEID)
            logger.warning('ERROR_QUOTES_%s: %s' % (id_text,e))
            quotes_worked = 0
            return 222222


        if quotes_worked == 1:
            num_quotes = df_quotes_beg_end.shape[0]
        
            # If there are NO QUOTES:
            if num_quotes == 0:
                #save_log(PATH_DATA + "/"  + "LOG/", 'NO_QUOTES', ARTICLEID)
                logger.warning('ERROR_NO_QUOTES: %s' % (id_text))
                return 333333
                
            # If there are QUOTES:
            else: 
                # Apply 'apply_ner_hug_face' function
                ls_entities_hug_face_orig = apply_ner_hug_face(PARAGRAPHS = paragraphs,     
                                                    MODEL = model, 
                                                    TOKENIZER = tokenizer) 
                # Remove UNdesirable entities
                ls_entities_hug_face = remove_entities_not_consider_from_ls_entities(LS_ENTITIES = ls_entities_hug_face_orig,
                                                                                    LS_ENTITIES_NOT_CONSIDER = list_entities_not_consider['entities'])
                                                                                    
                # If there are NO ENTITIES:
                if len(ls_entities_hug_face) == 0:
                    #save_log(PATH_DATA + "/"  + "LOG/", 'NO_ENTITIES IDENTIFIED', ARTICLEID)
                    logger.warning('ERROR_NO_ENTITIES_IDENTIFIED: %s' % id_text)
                    return 444444
                # If there are ENTITIES:
                else: 
                    # We take as entities only the ones obtained with hugging face library
                    df_entities = ls_entities_as_dataframe(ls_entities_hug_face)
                    
                                                                                    
                    ## -- ORGANIZE ENTITIES-- ###
                    try:
                        
                        list_all_about_entities = organize_entities(DF_POSTAG = df_postag,      
                                                NAMES_AUX = NAMES_AUX,      
                                                DF_QUOTES_BEG_END = df_quotes_beg_end, 
                                                DF_ENTITIES  = df_entities)

                        df_entities_gender_aux = list_all_about_entities[0]
                        df_all_entities = list_all_about_entities[1]
                        df_entities_postag = list_all_about_entities[2]

                        entities_worked = 1
                        logger.info(entities_worked)

                    except (Exception) as e:
                        #save_log(PATH_DATA + "/"  + "LOG/", "NO_ENTITIES", ARTICLEID)
                        logger.warning('ERROR_NO_ENTITIES_ORGANIZED_%s:  %s' % (id_text,e))
                        entities_worked = 0
                        return 555555                                             
            

                    logger.info('Passou de: organize_entities') 



                    # If there are entities and they were identified:
                    if entities_worked == 1:

                        ## ------------------------------------------------------------- ##
                        ## ------------------ QUOTE-ENTITY ASSIGNMENT ------------------ ##
                        ## ------------------------------------------------------------- ##

                        ## -- 1st evidence -- ###
                        ## -- APPROACH WITH VERBS -- ###
                        try:
                            ls_ent_quote_verbs = apply_verb_heur(df_quotes_beg_end, 
                                                                paragraphs,
                                                                df_postag,
                                                                df_all_entities)
                            verbs_df = ls_ent_quote_verbs[0]
                            df_quote_verbs = ls_ent_quote_verbs[1]
                            df_ent_quote_verbs = ls_ent_quote_verbs[2]
                            verbs_worked = 1

                        except (Exception) as e:
                            #save_log(PATH_DATA + "/"  + "LOG/", "ERROR_VERB", ARTICLEID)
                            logger.warning('ERROR-VERB_%s: %s' % (id_text,e))
                            verbs_worked = 0
                            
                            ## Fake object
                            df_ent_quote_verbs = assign_nan_to_all_quotes(df_quotes_beg_end)
                            df_ent_quote_verbs = df_ent_quote_verbs.rename(columns = {'entity_full_name':'ent_cand'})
                            df_ent_quote_verbs['ent_quote_dif_parag_verb'] = df_ent_quote_verbs.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
                            df_ent_quote_verbs['ent_quote_same_parag_verb'] = df_ent_quote_verbs.apply(lambda row: ent_quote_same_parag(row), axis = 1)
                            df_ent_quote_verbs = df_ent_quote_verbs.drop(columns = ['quote_text'])
                            df_ent_quote_verbs = df_ent_quote_verbs.rename(columns = {'ent_cand':'entity_verb',
                                                                    'id_parag_ent':'id_parag_ent_verb'})
                            
                            

                        logger.info('Passou de: apply_verb_heur')   
                        
                        if verbs_worked == 1:
                            ## -- 4th evidence -- ##
                            ## -- PRONOUNS -- ##
                            try:    
                                df_pron = apply_pron_heur(df_postag,
                                                        df_quote_verbs,
                                                        verbs_df,
                                                        df_quotes_beg_end,
                                                        df_entities_postag)
                            except (Exception) as e:
                                #save_log(PATH_DATA + "/"  + "LOG/", "ERROR_PRON", ARTICLEID)
                                logger.warning('ERROR-PRON_%s: %s' % (id_text,e))
                                
                                ## Fake object
                                df_pron = assign_nan_to_all_quotes(df_quotes_beg_end)
                                df_pron['ent_quote_dif_parag_pron'] = df_pron.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
                                df_pron['ent_quote_same_parag_pron'] = df_pron.apply(lambda row: ent_quote_same_parag(row), axis = 1)
                                df_pron = df_pron.drop(columns = ['quote_text', 'id_ent_beg', 'id_ent_end'])
                                df_pron = df_pron.rename(columns = {'entity_full_name':'entity_pron',
                                                                    'id_parag_ent':'id_parag_ent_pron'})
                        # If there are NO verbs we DON'T identify pronouns        
                        else: # verbs_worked == 0:
                                ## Fake object
                                df_pron = assign_nan_to_all_quotes(df_quotes_beg_end)
                                df_pron['ent_quote_dif_parag_pron'] = df_pron.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
                                df_pron['ent_quote_same_parag_pron'] = df_pron.apply(lambda row: ent_quote_same_parag(row), axis = 1)
                                df_pron = df_pron.drop(columns = ['quote_text', 'id_ent_beg', 'id_ent_end'])
                                df_pron = df_pron.rename(columns = {'entity_full_name':'entity_pron',
                                                                    'id_parag_ent':'id_parag_ent_pron'})
                                

                        logger.info('Passou de: apply_pron_heur')
        

                        ## -- 2nd evidence -- ###
                        ## -- APPROACH WITH DISTANCE -- ###
                        try:    
                            df_ent_quote_dist = apply_dist_heur(df_quotes_beg_end, 
                                                                df_entities_postag)
                            dist_worked = 1

                        except (Exception) as e:
                            #save_log(PATH_DATA + "/"  + "LOG/", "ERROR_DIST", ARTICLEID)
                            logger.warning('ERROR-DIST_%s: %s' % (id_text,e))
                            dist_worked = 0
                            
                            ## Fake object
                            df_ent_quote_dist = assign_nan_to_all_quotes(DF_QUOTES_BEG_END = df_quotes_beg_end)  
                            df_ent_quote_dist['ent_quote_dif_parag_dist'] = df_ent_quote_dist.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
                            df_ent_quote_dist['ent_quote_same_parag_dist'] = df_ent_quote_dist.apply(lambda row: ent_quote_same_parag(row), axis = 1)
                            df_ent_quote_dist = df_ent_quote_dist.drop(columns = ['quote_text', 
                                                                                'id_ent_beg', 'id_ent_end'])
                            df_ent_quote_dist = df_ent_quote_dist.rename(columns = {'entity_full_name':'entity_dist',
                                                                                    'id_parag_ent':'id_parag_ent_dist'})
                            
                            
                        
                        logger.info('Passou de: apply_dist_heur')


                        ## -- 3rd evidence -- ##
                        ## -- APPROACH WITH NOTES -- ##
                        try:    
                            df_note_quote_dist = apply_note_heur(df_postag, 
                                                                df_quotes_beg_end)
                        except (Exception) as e:
                            #save_log(PATH_DATA + "/"  + "LOG/", "ERROR_NOTE", ARTICLEID)
                            logger.warning('ERROR-NOTE_%s: %s' % (id_text,e))
                            
                            ## Fake object
                            df_note_quote_dist = assign_nan_to_all_quotes(DF_QUOTES_BEG_END = df_quotes_beg_end)  
                            df_note_quote_dist['ent_quote_dif_parag_note'] = df_note_quote_dist.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
                            df_note_quote_dist['ent_quote_same_parag_note'] = df_note_quote_dist.apply(lambda row: ent_quote_same_parag(row), axis = 1)
                            df_note_quote_dist = df_note_quote_dist.drop(columns = ['quote_text', 
                                                                                'id_ent_beg', 'id_ent_end'])
                            df_note_quote_dist = df_note_quote_dist.rename(columns = {'entity_full_name':'entity_note',
                                                                                    'id_parag_ent':'id_parag_ent_note'})
                            
                            

                        logger.info('Passou de: apply_note_heur')
                        
                        
                        ## ----------------------------- ##
                        ## -- Put everything together -- ##
                        ## ----------------------------- ##

                        try:
                            verbs_dist_note_pron = put_everything_together(df_ent_quote_verbs,
                                                                        df_ent_quote_dist,
                                                                        df_note_quote_dist,
                                                                        df_pron,
                                                                        df_quotes_beg_end)

                            ## -- To filter useful QUOTES -- ##
                            verbs_dist_note_pron = verbs_dist_note_pron[verbs_dist_note_pron['num_verb'] >= NUM_VERB_MIN]
                            verbs_dist_note_pron = verbs_dist_note_pron[verbs_dist_note_pron['tam_quote'] >= LENGTH_QUOTE_MIN]
                            verbs_dist_note_pron = verbs_dist_note_pron[verbs_dist_note_pron['quote_language'] == QUOTE_LANGUAGE]


                            # Define FINAL ENTITY
                            df = verbs_dist_note_pron_define_final_entity(VERBS_DIST_NOTE_PRON = verbs_dist_note_pron, 
                                                                        K = K) 


                            # Auxiliary object to add 'gender'
                            df_entities_gender_aux2 = df_entities_gender_aux[['entity_full_name', 
                                                                            'gender']]
                            df_entities_gender_aux2 = df_entities_gender_aux2.drop_duplicates()
                            df_entities_gender_aux2 = df_entities_gender_aux2.rename(columns = {'entity_full_name':'entity_final'})


                            # Merge/join data with 'gender'
                            df_gender = df.merge(df_entities_gender_aux2, 
                                    on = 'entity_final', 
                                    how = 'left')



                            df_gender = df_gender.drop_duplicates()



                            # Colunas/variaveis da base:
                            col_df = list(df_gender.columns.values)

                            # Fazer uma unica string com os nomes das colunas
                            # Essa string vai ser usada para salvar  abse em csv com a biblioteca numpy
                            header_df_file = 'article_id' 

                            for id_col in range(0, len(col_df)):
                                header_df_file = header_df_file + '\t' + col_df[id_col]

                            df_gender = df_gender.fillna('undefined')
                            
                            data = df_gender.to_dict(orient = 'records')
                            
                            
                            quotes_and_speakers = get_quotes_and_speakers(data)
                            unique_speakers = get_unique_speakers(data)
                            stats = get_statistics(quotes_and_speakers, unique_speakers)

                            logger.info('Identify speakers complete | %s' % id_text)
                            logger.info('## --------------------------------------------- ##')

                            #return quotes_and_speakers, unique_speakers, stats, df_gender, header_df_file
                            return quotes_and_speakers, unique_speakers, stats

                            

                        except (Exception) as e:
                            #save_log(PATH_DATA + "/" + "LOG/", "ERROR_FINALENTITY", ARTICLEID)
                            logger.warning('ERROR-FINALENTITY_%s: %s' % (id_text,e))


                            return 999999
                        
                    else: #  if entities_worked == 0:
                        pass

        else: #  if quotes_worked == 0:
            pass

    else: #  if nlp_worked == 1:
        pass 




    
"""

@logger.critical
def main():
    root_pah = os.getcwd()
    date = datetime.datetime.now().replace(second = 0, microsecond = 0)

    texts_file = os.path.join(*[root_pah,'text'])
    csv_file = os.path.join(*[root_pah,'csv',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    json_file = os.path.join(*[root_pah,'json',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    texts_read_file = os.path.join(*[root_pah,'text_read',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])

    texts_error_nlp_file = os.path.join(*[root_pah,'text_problems','text_error_nlp',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    text_error_quotes_file = os.path.join(*[root_pah,'text_problems','text_error_quotes',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    text_error_noquotes_file = os.path.join(*[root_pah,'text_problems','text_error_noquotes',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    texts_error_entities_organize_file = os.path.join(*[root_pah,'text_problems','text_error_entities_organize',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    texts_error_noentities_file = os.path.join(*[root_pah,'text_problems','text_error_noentities',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])
    texts_error_finalentity_file = os.path.join(*[root_pah,'text_problems','text_error_finalentity',date.strftime('%Y'), date.strftime('%m'), date.strftime('%d')])


    for path in [texts_file, csv_file, json_file, texts_read_file]:
        os.makedirs(path, exist_ok = True)

    for path in [texts_error_nlp_file, text_error_quotes_file, text_error_noquotes_file, texts_error_entities_organize_file, texts_error_noentities_file, texts_error_finalentity_file]:
        os.makedirs(path, exist_ok = True)


    all_files = [files for files in os.listdir(texts_file)]

    if all_files:

            
        for files in all_files:
            logger.info('Start Identify speakers | file: %s' % files)   
            
            ARTICLEID = files
            ARTICLEID_notxt = files[0:(len(files)-4)]           
            print('BEGIN: '+ str(ARTICLEID_notxt))

            text_filename = os.path.join(*[texts_file, files])
            csv_filename = os.path.join(*[csv_file, files.replace('.txt','.csv')])
            json_filename = os.path.join(*[json_file, files.replace('.txt','.json')])
            text_read_filename = os.path.join(*[texts_read_file, files])

            texts_error_nlp_filename = os.path.join(*[texts_error_nlp_file, files])
            text_error_quotes_filename = os.path.join(*[text_error_quotes_file, files])
            text_error_noquotes_filename = os.path.join(*[text_error_noquotes_file, files])
            texts_error_entities_organize_filename = os.path.join(*[texts_error_entities_organize_file, files])
            texts_error_noentities_filename = os.path.join(*[texts_error_noentities_file, files])
            texts_error_finalentity_filename = os.path.join(*[texts_error_finalentity_file, files])
            
            
            try:
                article_text = read_txtfile(PATH_NEWSTEXT = text_filename)
                res_identify_speakers = identify_speakers(text = article_text, NAMES_AUX = names_aux, PATH_DATA = root_pah, ARTICLEID = ARTICLEID, ARTICLEID_notxt = ARTICLEID_notxt)
                
                if isinstance(res_identify_speakers, int): 
                    if res_identify_speakers == 111111:
                        shutil.move(text_filename, texts_error_nlp_filename)

                    if res_identify_speakers == 222222:
                        shutil.move(text_filename, text_error_quotes_filename)

                    if res_identify_speakers == 333333:
                        shutil.move(text_filename, text_error_noquotes_filename)

                    if res_identify_speakers == 444444:
                        shutil.move(text_filename, texts_error_noentities_filename)

                    if res_identify_speakers == 555555:
                        shutil.move(text_filename, texts_error_entities_organize_filename)

                    if res_identify_speakers == 999999:
                        shutil.move(text_filename, texts_error_finalentity_filename)

                else:
                    quotes_and_speakers, unique_speakers, stats, df_gender, header_df_file =  res_identify_speakers
                    res = {"response" : {"quotes_and_speakers" : quotes_and_speakers, "unique_speakers" : unique_speakers, "statistics" : stats}}                        


                    save_file(ARTICLEID = ARTICLEID_notxt, DF = df_gender, PATH_SAVE = csv_file + '/', HEADER = header_df_file)
                    print('DONE: '+ str(ARTICLEID_notxt) + ' - ' + str(df_gender.shape[1]) + ' col')


                    #df_gender.to_csv(csv_filename, encoding='utf-8', index=False, sep='\t')            
                    logger.info('CSV file saved  | %s' % csv_filename)

                
                    with open(json_filename, 'w') as fp:
                        json.dump(res, fp)
                    logger.info('Json file saved | %s' % json_filename)

                logger.info('Identify speakers complete | %s' % files)
                logger.info('----------------------------------------')

                shutil.move(text_filename, text_read_filename)
            
            except:
                print('ERROR_MAIN: ' + ARTICLEID_notxt)
                save_log(root_pah + "LOG/", "ERROR_MAIN", ARTICLEID)
    else:
        logger.warning('There is no file to read, the directory: %s is empty' % texts_file)



if __name__ == "__main__":
    main()

"""