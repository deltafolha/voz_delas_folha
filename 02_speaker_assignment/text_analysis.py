import re            # regex_inside_doublequotes
import pandas as pd  # text_in_doublequotes
import numpy as np
import os
from os import listdir
from pathlib import Path
import spacy
import datetime
from spacy.language import Language
from spacy_langdetect import LanguageDetector
from langdetect import detect

from transformers import AutoModelForTokenClassification, AutoTokenizer
import torch

from log import Log
logger = Log('text_analysis',__name__)

# COUNT VARIABLES
NO_QUOTES_NO_ENTITIES = 0
NO_QUOTES_ENTITIES = 0 
QUOTES_NO_ENTITIES = 0
QUOTES_ENTITIES = 0
NO_GENDER = 0 
NO_CHARAC = 0
ERROR = 0

@logger.critical
def check_zero_quotation_marks(article_text):
    count = article_text.count("\"")
    if count == 0:
        return True
    return False


@logger.critical
def check_quotation_marks(article_text):
    count = article_text.count("\"")
    if count % 2 == 0:
        return True
    return False

# Add gender column based on IBGE data
# It returns a data.frame with:
### id_parag
### entity_original
### entity_original_upper
### single_name_original
### entity_full_name
### gender

@logger.critical
def add_gender_to_entities(DF_ENTITIES, NAMES_AUX):
    # Auxiliary object
    df_entities_aux = DF_ENTITIES.drop(columns = ['first_name', 
                                                  'family_name', 
                                                  'first_name_original'])

    # Split name in 2
    df_entities_aux[['first_name', 'family_name']] = df_entities_aux['entity'].str.split(' ', 1, expand = True)

    # Names in Capital letter
    df_entities_aux['first_name'] = df_entities_aux['first_name'].str.upper()
    df_entities_aux['family_name'] = df_entities_aux['family_name'].str.upper()

    # Remove accents from the names
    df_entities_aux['first_name'] = remove_accents(df_entities_aux['first_name']) 
    df_entities_aux['family_name'] = remove_accents(df_entities_aux['family_name'])

    # Update 'df_entities_aux' with gender
    df_entities_gender = df_entities_aux.merge(NAMES_AUX, 
                                               on = 'first_name',
                                               how = 'left') 

    df_entities_gender = df_entities_gender.rename(columns = {'entity':'entity_full_name'})

    # Auxiliary object
    df_entities_gender_aux = df_entities_gender.drop(columns = ['first_name', 'family_name'])
    
    return(df_entities_gender_aux)




# All entities in a data.frame
# This is used to identify an entity by part of the whole name
# It depends on: 'define_final_entity' function
# It returns a data.frame with:
### complete_name
### len_complete_name
### single_name
### single_name_upper
### single_name_original
### id_parag_all
### entity
@logger.critical
def all_entities_dataframe(DF_ENTITIES, DF_ENTITIES_PARAG, DF_INTERSEC):

    # All entities
    all_entities = DF_ENTITIES['entity'].values.tolist()

    # List that saves all distinct entities    
    list_all_entities_aux = []

    for ent in all_entities:
        ent_split = ent.split(" ")

        list_name = []
        for name in ent_split:
            list_name.append(name)

        dict_all_ent = {'complete_name': ent,
                        'len_complete_name': len(ent_split),
                        'single_name': list_name}
        df_name = pd.DataFrame(data = dict_all_ent)
        list_all_entities_aux.append(df_name)


    # Initiate a data frame with all names

    if len(list_all_entities_aux) == 1:
        df_all_entities = list_all_entities_aux[0]

    if len(list_all_entities_aux) > 1:   
        df_all_entities = pd.concat([list_all_entities_aux[0], 
                                         list_all_entities_aux[1]], 
                                         axis = 0, 
                                         ignore_index = True)

        for df in range(2, len(list_all_entities_aux)):
            df_all_entities = pd.concat([df_all_entities, list_all_entities_aux[df]], 
                                            axis = 0, ignore_index = True)    

    # Re-order names by ascending order
    df_all_entities = df_all_entities.sort_values(['complete_name'], ascending = [True]) 
    df_all_entities = df_all_entities.drop_duplicates()
    
    
    # Remove expressions that are not names (that are stopwords)
    list_not_names = ['de', 'dos', 'das', 'e', 'De', 'Dos', 'Das', 'E', 'da', 'Da', 'do', 'Do']

    df_all_entities['single_name_upper'] = df_all_entities['single_name'].str.upper()

    df_all_entities = df_all_entities[-df_all_entities["single_name"].isin(list_not_names)]


    # Keep original names
    df_all_entities['single_name_original'] = df_all_entities['single_name'] 
    # Remove accents from the names
    df_all_entities['single_name'] = remove_accents(df_all_entities['single_name']) 
    df_all_entities['single_name_upper'] = remove_accents(df_all_entities['single_name_upper'])
    
    ## -- -- ##
    # Join 'df_all_entities' and 'df_entities_parag'
    df_all_entities = df_all_entities.merge(DF_ENTITIES_PARAG, 
                                            left_on = 'complete_name',
                                            right_on = 'entity',
                                            how = 'left')
    # Rename column 'entity' to 'entity_orig'
    df_all_entities = df_all_entities.rename(columns = {'entity':'entity_orig'}) 
    
    
    # Deal with names that have intersection
    numrow_DF_INTERSEC = DF_INTERSEC.shape[0]
    
    # If there are names with intersection: deal with them
    if numrow_DF_INTERSEC >= 1:
        # Merge to get 'intersection' between names pair column
        df_all_entities = df_all_entities.merge(DF_INTERSEC, 
                                                on = 'complete_name',
                                                how = 'left')


        # 'entity' as the final version
        # If there is NO intersection between 2 names: Use the original version
        # If there is intersection between 2 names: Use the full/complete one
        df_all_entities['entity'] = df_all_entities.apply(lambda row: define_final_entity(row), axis = 1)

        # Remove auxiliary columns/variables
        df_all_entities = df_all_entities.drop(columns = ['entity_intersec'])
    
    # If there are NO names with intersection: use 'entity_orig'
    else:
        df_all_entities['entity'] = df_all_entities['entity_orig']
        
        
    # Auxiliary column to re-order rows
    df_all_entities = df_all_entities.assign(order = df_all_entities.index)
    # Sort rows by paragraph and the order entity appeared
    df_all_entities = df_all_entities.sort_values(by = ['id_parag', 'order'], ascending = [True, True])
    # Remove auxiliary column/variable
    df_all_entities = df_all_entities.drop(columns = 'order')
    # Remove duplicated entries
    df_all_entities = df_all_entities.drop_duplicates()
    

    # Remove accent from entity
    df_all_entities['entity'] = remove_accents(df_all_entities['entity'])
    
    
    # Rename 'id_parag'
    df_all_entities = df_all_entities.rename(columns = {'id_parag':'id_parag_all'})    
    
    return df_all_entities
    
    
    
# It needs:
## characterize_entities_given_gender
## characterize_entities_infer_gender
### id_ent_beg
### id_ent_end
### gender
### context_before_sent
### context_after_sent
@logger.critical
def apply_characterize_entities(DF_ENTITIES_POSTAG, DF_POSTAG, WINDOW_LENGTH):
    ls_characterize_entities = []
    
    for INDEX,ROW in DF_ENTITIES_POSTAG.iterrows():
        
        
        beg = ROW['id_ent_beg']
        end = ROW['id_ent_end']
        gender = ROW['gender']
                
        # If there is a known gender    
        if isinstance(gender, str):
            result = characterize_entities_given_gender(INDEX_BEG = beg, 
                                                        INDEX_END = end, 
                                                        GENDER = gender, 
                                                        DF_POSTAG = DF_POSTAG, 
                                                        WINDOW_LENGTH = WINDOW_LENGTH)
        # If gender is unknown
        else:
            result = characterize_entities_infer_gender(INDEX_BEG = beg, 
                                                        INDEX_END = end, 
                                                        DF_POSTAG = DF_POSTAG, 
                                                        WINDOW_LENGTH = WINDOW_LENGTH)

        ls_characterize_entities.append(result)
    
    # Make it a data.frame
    df_characterize_entities = pd.concat(ls_characterize_entities)
    
    # Auxiliary to get the entity by its begin and end
    df_ents_postag = DF_ENTITIES_POSTAG[['id_ent_beg', 'id_ent_end', 'entity', 'entity_full_name']]
    df_ents_postag = df_ents_postag.drop_duplicates()
    
    # 'df_characterize_entities' updated with the entity itself
    df_characterize_entities = df_characterize_entities.merge(df_ents_postag, 
                                                             on = ['id_ent_beg', 'id_ent_end'],
                                                             how = 'left')
    
    df_characterize_entities = df_characterize_entities.drop_duplicates()
    
    return(df_characterize_entities)    




## --- Use Hugging face model to NER --- ##
# It returns:
## A list with arrays. Each array has a pair:
### paragraph number
### entity
@logger.critical
def apply_ner_hug_face(PARAGRAPHS, MODEL, TOKENIZER):
    
    ls_entities = []
    
    num_pg = len(PARAGRAPHS)
    id_pg = range(0, num_pg) 

    # Apply entity recognition model by paragraphs & Keep only the PERSON Entity entries
    for pg in id_pg:
        parag = PARAGRAPHS[pg]
        
        # tokenization
        inputs = TOKENIZER(parag, 
                       max_length = 512, 
                       truncation = True, 
                       return_tensors = "pt")
        tokens = inputs.tokens()

        # get predictions
        outputs = MODEL(**inputs).logits
        predictions = torch.argmax(outputs, dim=2)


        # Save predictions into lists
        token_list = []
        label_list = []

        # A prediction for each token
        for token, prediction in zip(tokens, predictions[0].numpy()):
            label = MODEL.config.id2label[prediction]
            if 'PESSOA' in label:
                token_list.append(token)
                label_list.append(label)
                
                
        ## --- Adjustments --- ##
        # Adjustments 00: if there is a sequence of syllables
        token_list_aux = token_list
        num_tokens_orig = len(token_list) - 1
        
        for i in range(num_tokens_orig, 0, -1):
            if (('##' in token_list[i]) and ('##' in token_list[i - 1])):
                token_i_nohash = token_list[i].replace("##", "")
                
                token_list_aux[i - 1] = token_list[i - 1] + token_i_nohash
                token_list_aux[i] = 'REMOVE'
            
            
        dict_tokens_orig = {'token': token_list,
                            'token_aux': token_list_aux,
                            'label': label_list
            }
        df_label_seq_syllables = pd.DataFrame(data = dict_tokens_orig)
        df_label_seq_syllables = df_label_seq_syllables[df_label_seq_syllables['token_aux'] != 'REMOVE']

        
        num_tokens = len(df_label_seq_syllables.token.values)

        token_list = df_label_seq_syllables.token.values.tolist()
        token_list_aux = df_label_seq_syllables.token.values.tolist()
        

        # Adjustments 01: to make 'Nel' and "##son" a single word 'Nelson', for instance
        for i in range(1, num_tokens):
            token = token_list[i]
            if '##' in token:
                token_nohash = token.replace("##", "")
                token_list_aux[i-1] = token_list[i-1] + token_nohash
                token_list_aux[i] = "REMOVE"
            else:
                continue




        dict_ent_hug_face_aux = {'token': df_label_seq_syllables.token.values.tolist(),
                                 'label': df_label_seq_syllables.label.values.tolist(),
                                 'token_aux': token_list_aux
                                 }
        df_label_syl = pd.DataFrame(data = dict_ent_hug_face_aux)
        
        df_label_syl = df_label_syl[df_label_syl['token_aux'] != 'REMOVE']
        
        # Adjustments 02: to make 'Nelson' and 'Rodrigues' a single entity 'Nelson Rodrigues', for instance
        ent_list = df_label_syl.token.values.tolist()
        label_list = df_label_syl.label.values.tolist()
        ent_list_aux = df_label_syl.token_aux.values.tolist()
        ent_update_list = df_label_syl.token_aux.values.tolist()

        num_ent = len(ent_list)

        for i in range(1, num_ent):
            if ((label_list[i - 1] == 'B-PESSOA') and (label_list[i] == 'I-PESSOA')):
                ent_update_list[i - 1] = ent_list_aux[i - 1] + ' ' + ent_list_aux[i]
                ent_list_aux[i-1] = np.nan
                ent_update_list[i] = 'REMOVE'
            else:
                continue



        dict_ent_hug_face = {'token': ent_list,
                             'label': label_list,
                             'token_aux': ent_list_aux,
                             'token_update': ent_update_list}
        df_ent_hug_face = pd.DataFrame(data = dict_ent_hug_face)
        df_ent_hug_face = df_ent_hug_face[df_ent_hug_face['token_update'] != 'REMOVE']

        
        ## --- Final object to return --- ##
        # Add results for the paragraph to 'ls_entities'
        for name in df_ent_hug_face.token_update.values.tolist():
            ls_entities.append((pg, name))
    
        
    return ls_entities



     
# Input:
### PARAGRAPHS is a list
### NLP is spacy object
### ENT_NOT_CONS is a list of strings not to be considered as entitities
# Output: 02 lists in a list:
## (0) df_entities:
### id_parag: paragraph index 
### entity: name itself
### first_name: only first name in capital letters
### family_name: the remain name in capital letters
## (1) df_postag:
### id_parag: paragraph index
### word: word itselt
### pos_tag: label
### gender: F, M or NaN
### number: Sing, Plu or NaN
@logger.critical
def apply_nlpmodels(PARAGRAPHS, NLP, ENT_NOT_CONS): 
    ls_entities = []
    ls_postag = []
    
    num_pg = len(PARAGRAPHS)
    id_pg = range(0, num_pg)  
    # Apply entity recognition model by paragraphs & Keep only the PERSON Entity entries
    for pg in id_pg:
        parag = PARAGRAPHS[pg]
        paragraph_without_quotes = re.sub(r'“.*?”|".*?"', '', parag)

        paragraph_nlp = NLP(parag)
        
        entities_nlp = NLP(paragraph_without_quotes)
        
        
        ents = [(e.text) for e in entities_nlp.ents if e.label_ == "PER"]
        
        # To iterate through entitites to save paragraph and the entity itself, 
        # if the entity is not at the prohibited list
        for people in ents:
            # Filtering entities to remove 'Covid', 'Deus' and Nao
            if people not in ENT_NOT_CONS:
                # Filtering entities to accept only PROPN
                for token in paragraph_nlp:
                    if token.pos_ == "PROPN":
                        if token.text in people:
                            aux = (pg, people)
                            # check for duplicates
                            if aux not in ls_entities:
                                ls_entities.append(aux)
            
        #id_word = []
        word = []
        postag = []
        gender = []
        number = []

        num_tk = len(paragraph_nlp)
        id_tk = range(0, num_tk) 
    
       
        
        # To iterate through words to save POS TAGS
        for tk in id_tk:
            token = paragraph_nlp[tk] 
            
            #id_word.append(tk)  
            
            word.append(token.text)  
            
            postag.append(token.pos_)
    
          
            if len(token.morph.get("gender")) > 0:
                if('f' in token.morph.get("gender")):
                    gender_found = "F"
                elif('m' in token.morph.get("gender")):
                    gender_found = "M"
                
                gender.append(gender_found) 
            else:
                gender.append(np.nan)
        
        
            if len(token.morph.get("number")) > 0:
                if('sing' in token.morph.get("number")):
                    number_found = "Sing"
                elif('plur' in token.morph.get("number")):
                    number_found = "Plu"            
                    
                number.append(number_found) 
            else:
                number.append(np.nan) 
    
    
        dict_pos = {'id_parag': pg,
                    #'id_word': id_word,
                    'word': word, 
                    'pos_tag': postag,
                    'gender': gender,
                    'number': number}
  
        df_pos = pd.DataFrame(data = dict_pos)
    
        ls_postag.append(df_pos)
    
    return [ls_entities, ls_postag]
    
    
    
# It needs:
### assign_entity_quote  
@logger.critical  
def apply_dist_heur(df_quotes_beg_end, 
		    df_entities_postag):
    
    id_pair = []
    id_parag = []
    id_quote_beg = []
    id_quote_end = []
    quote_text = []
    entity = []
    entity_full_name = []
    id_parag_ent = []
    id_ent_beg = []
    id_ent_end = []

    numRows = df_quotes_beg_end.shape[0]

    
    for i in range(0, numRows):
        
        quote_pair = df_quotes_beg_end.iloc[i]['id_pair']
        
        entity_quote = assign_entity_quote(quote_pair, df_quotes_beg_end, df_entities_postag)
        
        entity_quote = entity_quote.drop_duplicates()
        
        id_pair.append(quote_pair)

        id_parag.append(int(entity_quote['id_parag']))

        id_quote_beg.append(int(entity_quote['id_quote_beg']))

        id_quote_end.append(int(entity_quote['id_quote_end']))

        quote_text.append(entity_quote['quote_text'][0])

        entity.append(entity_quote['entity'][0])

        entity_full_name.append(entity_quote['entity_full_name'][0])

        

        if np.isnan(entity_quote['id_parag_ent'][0]): 
            id_parag_ent.append(np.nan)
        else:
            id_parag_ent.append(int(entity_quote['id_parag_ent'][0]))
        if np.isnan(entity_quote['id_ent_beg'][0]): 
            id_ent_beg.append(np.nan)
        else:
            id_ent_beg.append(int(entity_quote['id_ent_beg'][0]))

        if np.isnan(entity_quote['id_ent_end'][0]): 
            id_ent_end.append(np.nan)
        else:
            id_ent_end.append(int(entity_quote['id_ent_end'][0]))


    df_ent_quote_dist = pd.DataFrame(list(zip(id_pair, id_parag, id_quote_beg, id_quote_end, 
                                              quote_text, entity, 
                                              entity_full_name,
                                              id_parag_ent, id_ent_beg, id_ent_end)),
                                    columns = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 
                                               'quote_text', 'entity', 
                                               'entity_full_name',
                                               'id_parag_ent', 'id_ent_beg', 'id_ent_end'])

    # Add column/variable   
    df_ent_quote_dist['ent_quote_dif_parag_dist'] = df_ent_quote_dist.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
    df_ent_quote_dist['ent_quote_same_parag_dist'] = df_ent_quote_dist.apply(lambda row: ent_quote_same_parag(row), axis = 1)

    ## Rename columns
    df_ent_quote_dist = df_ent_quote_dist.drop(columns = ['entity', 'quote_text', 'id_ent_beg', 'id_ent_end'])

    df_ent_quote_dist = df_ent_quote_dist.rename(columns = {'entity_full_name':'entity_dist',
                                                            'id_parag_ent':'id_parag_ent_dist'
                                                           })
    return df_ent_quote_dist  
    
    
  
# It needs:
### recognize_note_terms_put_as_df_entities    
### entities_postag_format
### assign_entity_quote
@logger.critical   
def apply_note_heur(df_postag, df_quotes_beg_end):    
    
    TERMOS_NOTA = ['NOTA', 'COMUNICADO', 'ASSESSORIA', 'TRECHO', 'TEXTO']  
    termos_nota_postag_df_como_df_entities_orig = recognize_note_terms_put_as_df_entities(NOTE_LIST = TERMOS_NOTA,
                                                                                          DF_POSTAG = df_postag)
    
    numExprNotas = termos_nota_postag_df_como_df_entities_orig.shape[0]
    numRows = df_quotes_beg_end.shape[0]
    
    id_pair = []
    id_parag = []
    id_quote_beg = []
    id_quote_end = []
    quote_text = []
    entity_full_name = []
    id_parag_ent = []
    id_ent_beg = []
    id_ent_end = []
    
    if numExprNotas > 0:
    
        termos_nota_postag = entities_postag_format(df_postag, 
                                                    termos_nota_postag_df_como_df_entities_orig)



        for i in range(0, numRows):
            quote_pair = df_quotes_beg_end.iloc[i]['id_pair']

            entity_quote = assign_entity_quote(quote_pair, 
                                                   df_quotes_beg_end, 
                                                   termos_nota_postag)

            id_pair.append(quote_pair)

            id_parag.append(int(entity_quote['id_parag']))

            id_quote_beg.append(int(entity_quote['id_quote_beg']))

            id_quote_end.append(int(entity_quote['id_quote_end']))

            quote_text.append(entity_quote['quote_text'][0])

            #entity_full_name.append(entity_quote['entity'][0])
            # All expressions are going to be the same
            entity_full_name.append('NOTA')


            if np.isnan(entity_quote['id_parag_ent'][0]): 
                id_parag_ent.append(np.nan)
            else:
                id_parag_ent.append(int(entity_quote['id_parag_ent'][0]))
            if np.isnan(entity_quote['id_ent_beg'][0]): 
                id_ent_beg.append(np.nan)
            else:
                id_ent_beg.append(int(entity_quote['id_ent_beg'][0]))

            if np.isnan(entity_quote['id_ent_end'][0]): 
                id_ent_end.append(np.nan)
            else:
                id_ent_end.append(int(entity_quote['id_ent_end'][0]))


        df_note_quote_dist = pd.DataFrame(list(zip(id_pair, id_parag, id_quote_beg, id_quote_end, 
                                                  quote_text, entity_full_name,
                                                       id_parag_ent, id_ent_beg, id_ent_end)),
                                        columns = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 
                                                  'quote_text', 'entity_full_name', 
                                                   'id_parag_ent', 'id_ent_beg', 'id_ent_end'])
        
    else:

        df_note_quote_dist = assign_nan_to_all_quotes(df_quotes_beg_end)


    # Add a column/variable to say if quote and entity are in the same paragraph
    df_note_quote_dist['ent_quote_dif_parag_note'] = df_note_quote_dist.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
    df_note_quote_dist['ent_quote_same_parag_note'] = df_note_quote_dist.apply(lambda row: ent_quote_same_parag(row), axis = 1)



    ## -- RENAME COLUMNS/VARIABLES -- ##
    df_note_quote_dist = df_note_quote_dist.drop(columns = ['quote_text', 'id_ent_beg', 'id_ent_end'])
    df_note_quote_dist = df_note_quote_dist.rename(columns = {'entity_full_name':'entity_note',
                                                                'id_parag_ent':'id_parag_ent_note'}
                                                  )
    
    return df_note_quote_dist

      
    
    
# It needs:
### recognize_pronouns_put_as_df_all_entities   
### assign_ent_quote_verbs 
### assign_entity_quote_pron
### ent_quote_dif_parag
### ent_quote_same_parag
@logger.critical
def apply_pron_heur(df_postag,
                        df_quote_verbs,
                        verbs_df,
                        df_quotes_beg_end,
                        df_entities_postag):     
    PRONOUNS_LIST = ['ELE', 'ELA']
    
    # Identify pronouns in the text
    df_quotes_beg_end_aux = df_quotes_beg_end[['id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text']]
        
    termos_pron_postag_df_como_df_all_entities_list = recognize_pronouns_put_as_df_all_entities(PRONOUNS_LIST = PRONOUNS_LIST, 
                                                                                                DF_POSTAG = df_postag,
                                                                                                DF_QUOTES_BEG_END = df_quotes_beg_end_aux)
    
    # If there are NO pronouns
    if isinstance(termos_pron_postag_df_como_df_all_entities_list, int):
        #print('NO pronouns recognized')
        df_pron = assign_nan_to_all_quotes(df_quotes_beg_end)
        
    # If there are pronouns
    else:
        termos_pron_postag_df_como_df_all_entities = termos_pron_postag_df_como_df_all_entities_list[1]
        df_prons_identified_postag = termos_pron_postag_df_como_df_all_entities_list[0]
        
        
        # If there are NO quotes assigned to verbs
        if isinstance(df_quote_verbs, int):
            #print('NO quotes assigned to verbs')
            df_pron_after_verb_aux = assign_nan_to_all_quotes(df_quotes_beg_end)

        # If there are quotes assigned to verbs
        else:
            #print('Quotes assigned to verbs')

            ## Pronoun immediately after VERBS - conservative approach
            pron_imed_after_verb = assign_ent_quote_verbs(DF_QUOTES_BEG_END = df_quote_verbs,  
                                                           DF_POSTAG = df_postag, 
                                                           DF_ALL_ENTS = termos_pron_postag_df_como_df_all_entities, 
                                                           DF_VERBS = verbs_df)

            # Add new column to 'df_quote_verbs'
            df_ent_quote_verbs_pron = df_quote_verbs.assign(pronoun = pron_imed_after_verb)

            # Select and reorder columns
            df_ent_quote_verbs_pron = df_ent_quote_verbs_pron[['id_pair', 'id_parag', 
                                                     'id_quote_beg', 'id_quote_end', 
                                                     'quote_text', 'word', 
                                                     'verb_before_quote', 'verb_after_quote', 
                                                     'no_citation_verb','pronoun']]

            # Consider quotes that have a pronoun associated
            df_ent_quote_verbs_pron = df_ent_quote_verbs_pron[df_ent_quote_verbs_pron['pronoun'] != "Undefined" ] 
            df_ent_quote_verbs_pron = df_ent_quote_verbs_pron.dropna(subset = ['pronoun'])


            # Gender from pronouns
            gender_aux = pd.DataFrame(['ele', 'ela', 'Ele', 'Ela'], columns = ['pronoun'])
            gender_aux = gender_aux.assign(gender = ['M', 'F', 'M', 'F'])

            df_ent_quote_verbs_pron_gender = df_ent_quote_verbs_pron.merge(gender_aux,
                                                                   on = 'pronoun',
                                                                   how = 'left')


            numRows = df_quotes_beg_end.shape[0]
            numExprPron = df_ent_quote_verbs_pron_gender.shape[0]
            id_quote_pron = df_ent_quote_verbs_pron_gender['id_pair'].tolist()

            list_pron = []


            # If there are pronouns
            if numExprPron > 0:

                for i in range(0, numRows): 
                    id_pair = df_quotes_beg_end.iloc[i]['id_pair']

                    if id_pair in id_quote_pron:

                        entity_quote = assign_entity_quote_pron(PAIR = id_pair, 
                                                            DF_QUOTES_BEG_END = df_quotes_beg_end, 
                                                            DF_ENTITIES_POSTAG = df_entities_postag, 
                                                            DF_PRON_QUOTE_DIST= df_ent_quote_verbs_pron_gender)
                        list_pron.append(entity_quote)
                    else:
                        dict_entity_quote = {'id_pair': id_pair,
                                             'id_parag': df_quotes_beg_end.iloc[i]['id_parag'],
                                             'id_quote_beg': df_quotes_beg_end.iloc[i]['id_quote_beg'],
                                             'id_quote_end': df_quotes_beg_end.iloc[i]['id_quote_end'], 
                                             'quote_text': df_quotes_beg_end.iloc[i]['quote_text'],
                                             'entity': np.nan,
                                             'entity_upper': np.nan,
                                             'entity_full_name': np.nan, 
                                             'id_parag_ent': np.nan,
                                             'id_ent_beg': np.nan,
                                             'id_ent_end': np.nan}

                        df_entity_quote = pd.DataFrame(data = dict_entity_quote, index=[0])
                        list_pron.append(df_entity_quote)


                if len(list_pron) >= 1:
                    df_pron_after_verb_aux = list_to_dataframe(list_pron)

            # If there are NO pronouns
            else:
                df_pron_after_verb_aux = assign_nan_to_all_quotes(df_quotes_beg_end)
                
                
        ## ------------------------------ ##
        ## -- Split data into 02 parts -- ##
        ## ------------------------------ ##
        # Drop columns, if needed

        df_pron_after_verb_aux_cols = list(df_pron_after_verb_aux.columns.values)
        if 'entity_upper' in df_pron_after_verb_aux_cols:
            df_pron_after_verb_aux = df_pron_after_verb_aux.drop(columns = ['entity_upper'])
        if 'entity' in df_pron_after_verb_aux_cols:
            df_pron_after_verb_aux = df_pron_after_verb_aux.drop(columns = ['entity'])


        # More conservative approach
        df_pron_after_verb = df_pron_after_verb_aux.loc[pd.notnull(df_pron_after_verb_aux.entity_full_name)]

        # No pronoun immediately after verb
        df_no_pron_after_verb = df_pron_after_verb_aux[df_pron_after_verb_aux['entity_full_name'].isnull()]


        # If there are quotes with NO pronouns immediately after
        if df_no_pron_after_verb.shape[0] > 0:
            #print('there are quotes with NO pronouns immediately after')
            df_near_quote_pron = nearest_quote_pron(DF_QUOTES_BEG_END = df_no_pron_after_verb, 
                                                   DF_PRONS_IDENTIFIED_POSTAG = df_prons_identified_postag)


            num_near_quote_pron = df_near_quote_pron.shape[0]

            # Remove column and drop duplicated rows from 'df_entities_postag'
            df_entities_postag_cols = list(df_entities_postag.columns.values)
            if 'single_name_original' in df_entities_postag_cols:
                df_entities_postag_aux = df_entities_postag.drop(columns = 'single_name_original').drop_duplicates()
            else:
                df_entities_postag_aux = df_entities_postag

            list_ent_pron_far_from_verb = []

            for i in range(0, num_near_quote_pron):

                quote_pair = df_near_quote_pron.iloc[i]['id_pair']

                entity_quote_pron_far_from_verb = assign_entity_quote_pron_far_from_verb(PAIR = quote_pair, 
                                                                                             DF_ENTITIES_POSTAG = df_entities_postag_aux, 
                                                                                             DF_NEAR_QUOTE_PRON = df_near_quote_pron)

                entity_quote_pron_far_from_verb = entity_quote_pron_far_from_verb.drop(columns = ['entity'])

                if 'entity' in list(entity_quote_pron_far_from_verb.columns.values):
                    entity_quote_pron_far_from_verb = entity_quote_pron_far_from_verb.drop(columns = ['entity'])


                if 'entity_upper' in list(entity_quote_pron_far_from_verb.columns.values):
                    entity_quote_pron_far_from_verb = entity_quote_pron_far_from_verb.drop(columns = ['entity_upper'])

                list_ent_pron_far_from_verb.append(entity_quote_pron_far_from_verb)


            if len(list_ent_pron_far_from_verb) >= 1:
                df_pron_far_from_verb = list_to_dataframe(list_ent_pron_far_from_verb)    

            # Rbind 'df_pron_after_verb' and 'df_no_pron_after_verb' DataFrames
            df_pron = pd.concat([df_pron_far_from_verb, 
                                df_pron_after_verb],           
                                ignore_index = True,
                                sort = False)

            df_pron = df_pron.sort_values(['id_pair'], ascending = [True]) 

        # If ALL quotes have pronouns immediately after
        else:
            #print('ALL quotes have pronouns immediately after')
            df_pron = df_pron_after_verb

            
    # Add a column/variable to say if quote and entity are in the same paragraph
    df_pron['ent_quote_dif_parag_pron'] = df_pron.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
    df_pron['ent_quote_same_parag_pron'] = df_pron.apply(lambda row: ent_quote_same_parag(row), axis = 1)

    # Remove and name columns
    df_pron = df_pron.drop(columns = ['quote_text', 'id_ent_beg', 'id_ent_end'])
    if 'entity_upper' in list(df_pron.columns.values):
        df_pron = df_pron.drop(columns = ['entity_upper'])
    if 'entity' in list(df_pron.columns.values):
        df_pron = df_pron.drop(columns = ['entity'])
        
    df_pron = df_pron.rename(columns = {'entity_full_name':'entity_pron',
                                            'id_parag_ent':'id_parag_ent_pron'})
    
    return df_pron
                                                                                           
 

    
    
    
    
    
    
# It needs:    
### assign_quote_verbs
### assign_ent_quote_verbs
### define_entity_paragraph
### ent_quote_dif_parag
### ent_quote_same_parag
@logger.critical
def apply_verb_heur(df_quotes_beg_end, 
                    paragraphs,
                    df_postag,
                    df_all_entities):


    VERBS = ['AFIRMA', 'AFIRMOU',
                 'CITA', 'CITOU',
                 'CONTA', 'CONTOU',
                 'DECLARA', 'DECLAROU',
                 'DESCREVE', 'DESCREVEU',
                 'ELUCIDA', 'ELUCIDOU',
                 'ESCREVE', 'ESCREVEU',
                 'EXPLICA', 'EXPLICOU',
                 'DIZ', 'DISSE',
                 'FALA', 'FALOU',
                 'FRISA', 'FRISOU',
                 'INFORMA', 'INFORMOU',
                 'LISTA', 'LISTOU',
                 'PONTUA', 'PONTUOU'
                 ]
    verbs_df = pd.DataFrame(VERBS, columns = ['word_upper'])
    verbs_df = verbs_df.assign(pos_tag = 'VERB')
    verbs_df = verbs_df.assign(word_citation = 1)

    df_quote_verbs = assign_quote_verbs(DF_QUOTES_BEG_END = df_quotes_beg_end,   
                                            LIST_VERBS = VERBS,
                                            PARAGRAPHS = paragraphs,
                                            DF_POSTAG = df_postag,
                                            DF_ALL_ENTS = df_all_entities)
    
    # If there are NO quotes assigned to VERBS:
    if isinstance(df_quote_verbs, int):
    
    	df_ent_quote_verbs = assign_nan_to_all_quotes(df_quotes_beg_end)
    	df_ent_quote_verbs = df_ent_quote_verbs.rename(columns = {'entity_full_name':'ent_cand'})
 


        
    # If there are quotes assigned to VERBS:
    else:
        list_ent_cand = assign_ent_quote_verbs(DF_QUOTES_BEG_END = df_quote_verbs,  
                                               DF_POSTAG = df_postag, 
                                               DF_ALL_ENTS = df_all_entities, 
                                               DF_VERBS = verbs_df)

        # Add new column to 'df_quote_verbs'
        df_ent_quote_verbs = df_quote_verbs.assign(ent_cand = list_ent_cand)

        # Add a column to 'df_ent_quote_verbs' to represent entity paragraph (the same of the quote)
        df_ent_quote_verbs['id_parag_ent'] = df_ent_quote_verbs.apply(lambda row: define_entity_paragraph(row), axis = 1)



        # Select and reorder columns
        df_ent_quote_verbs = df_ent_quote_verbs[['id_pair', 'id_parag', 
                                                     'id_quote_beg', 'id_quote_end', 
                                                     'quote_text', 
                                                     'word_citation',
                                                     'ent_cand',
                                                     'id_parag_ent']]

        
        
    df_ent_quote_verbs['ent_quote_dif_parag_verb'] = df_ent_quote_verbs.apply(lambda row: ent_quote_dif_parag(row), axis = 1)
    df_ent_quote_verbs['ent_quote_same_parag_verb'] = df_ent_quote_verbs.apply(lambda row: ent_quote_same_parag(row), axis = 1)

    ## Rename columns
    df_ent_quote_verbs = df_ent_quote_verbs.drop(columns = ['quote_text'])

    df_ent_quote_verbs = df_ent_quote_verbs.rename(columns = {'ent_cand':'entity_verb',
                                                            'id_parag_ent':'id_parag_ent_verb'}
                                                    )
    
    return [verbs_df, df_quote_verbs, df_ent_quote_verbs]      
    
    
    
    

# It returns a data.frame with:
### id_pair
### id_parag 
### id_quote_beg
### id_quote_end
### quote_text'
### entity
### entity_upper
### entity_full_name
### id_parag_ent
### id_ent_beg
### id_ent_end'
@logger.critical
def assign_entity_no_ties(DF_PAIR_QUOTES, DF_ENT_CAND):
    
    # Put 'id_ent_beg' explicitly 
    df_ent_assigned_noties_aux = DF_PAIR_QUOTES.assign(id_ent_beg = int(DF_ENT_CAND['id_ent_beg']))

    # Use 'id_ent_beg' to get 'everything else'
    df_ent_assigned_noties = df_ent_assigned_noties_aux.merge(DF_ENT_CAND,
                                                              on = ['id_ent_beg'],
                                                              how = 'left')

    # Rename columns/variables
    df_ent_assigned_noties = df_ent_assigned_noties.rename(columns = {'id_parag_x':'id_parag', 
                                                                      'id_parag_y':'id_parag_ent',
                                                                      'gender_x':'gender_pron', 
                                                                      'gender_y':'gender'})
    
    # Remove columns/variables related to pronouns
    df_ent_assigned_noties = df_ent_assigned_noties.drop(columns= [#'id_pronoun', 
                                                                   'pronoun',
                                                                   #'pron_inside_quote', 
                                                                    'gender_pron'])
    
    # Reorder columns/variables
    order_cols = ['id_pair', 'id_parag', 
                  'id_quote_beg', 'id_quote_end', 'quote_text',
                  'entity', 'entity_upper', 'entity_full_name',
                  'id_parag_ent', 'id_ent_beg', 'id_ent_end']

    
    df_ent_assigned_noties = df_ent_assigned_noties.reindex(columns = order_cols)

                                                    
 
    return df_ent_assigned_noties
    
    
    
    
# It uses 'closer_ent_from_quote_pair'
# It returns:
## a dataframe
@logger.critical
def assign_entity_quote(PAIR, DF_QUOTES_BEG_END, DF_ENTITIES_POSTAG):
    ### -- ARGUMENTS -- ###
    #PAIR = 2
    #DF_QUOTES_BEG_END = df_quotes_beg_end 
    #DF_ENTITIES_POSTAG = df_entities_postag
    
    ### -- FUNCTION -- ###
    df_pair_quotes = DF_QUOTES_BEG_END.query('id_pair == ' + str(PAIR)) 

    # pair of quotes paragraph
    parag = df_pair_quotes['id_parag'].drop_duplicates().tolist()
    
    # How many entities were identified at this paragraph:
    ent_candidates = DF_ENTITIES_POSTAG.query('id_parag == ' + str(parag))

    num_candidates = len(ent_candidates)
    
    ### Single entity candidate - easiest case
    if num_candidates == 1: 
        df_ent_assigned = df_pair_quotes.merge(ent_candidates,
                                    on = 'id_parag',
                                    how = 'left')
        col_drop_num_cand_1 = ['tam_quote', 'quote_language', 'num_dif_grammar_class', 'num_verb', 'num_noun']
        # Add 'id_parag_ent' column/variable
        df_ent_assigned = df_ent_assigned.assign(id_parag_ent = df_ent_assigned['id_parag']) 
        df_ent_assigned = df_ent_assigned.drop(columns = col_drop_num_cand_1)
        # Reorder columns
        order_cols_df_ent_assigned = ['id_pair', 'id_parag', 
                                      'id_quote_beg', 'id_quote_end', 
                                      'quote_text', 
                                      'entity', 'entity_upper', 'entity_full_name', 
                                      'id_parag_ent', 'id_ent_beg', 'id_ent_end']
        df_ent_assigned = df_ent_assigned.reindex(columns = order_cols_df_ent_assigned)
        
        df_ent_assigned = df_ent_assigned.drop_duplicates()
        
        return df_ent_assigned
        
    ### More than an entity candidate - 'desempatar'
    if num_candidates > 1: 
        
        df_ent_assigned = closer_ent_from_quote_pair(ent_candidates, df_pair_quotes)  
        
        df_ent_assigned = df_ent_assigned.drop_duplicates()
        
        return df_ent_assigned
    
    ### No candidate
    if num_candidates == 0:
        # paragraph of Entity candidates before a given paragraph
        ent_candid_before_parag = DF_ENTITIES_POSTAG.loc[(DF_ENTITIES_POSTAG['id_parag'] < parag[0])]
        
        # Sort paragraphs descending order
        parag_with_cand_entities = ent_candid_before_parag.sort_values('id_parag', ascending = False)
        
        # 'paragraph of Entity candidates before a given paragraph' with no duplicates
        all_parag_with_cand_entities = parag_with_cand_entities['id_parag'].drop_duplicates()
        
        num_parag_try = len(all_parag_with_cand_entities)
        
        # If it is the 1st paragraph there is no paragraph before to try and we return nan
        if num_parag_try == 0:
                dict_no_ent_bef = {'id_pair': str(PAIR),
                                   'id_parag': parag,
                                   'id_quote_beg': df_pair_quotes['id_quote_beg'].drop_duplicates().tolist(),
                                   'id_quote_end': df_pair_quotes['id_quote_end'].drop_duplicates().tolist(),
                                   'quote_text': df_pair_quotes['quote_text'].drop_duplicates().tolist(),
                                   'entity': [np.nan],
                                   'entity_upper': [np.nan],
                                   'entity_full_name': [np.nan],
                                   'id_parag_ent': [np.nan],
                                   'id_ent_beg': [np.nan],
                                   'id_ent_end': [np.nan]}
                df_no_ent_bef = pd.DataFrame(dict_no_ent_bef)
                
                df_no_ent_bef = df_no_ent_bef.drop_duplicates()
                
                return df_no_ent_bef
            
    # If there are paragraphs before to try
        else:
            for row in range(0, num_parag_try):
                parag_try = all_parag_with_cand_entities.iloc[row]
            
                ent_candidates_try = ent_candid_before_parag.query('id_parag == ' + str(parag_try))
            
                num_candidates = len(ent_candidates_try)
                
                if num_candidates == 1:
                    # Put 'id_ent_beg' explicitly 
                    df_ent_assigned = df_pair_quotes.assign(id_ent_beg = int(ent_candidates_try['id_ent_beg']))
                    # Use 'id_ent_beg' to get 'word'
                    df_ent_assigned = df_ent_assigned.merge(ent_candidates_try,
                                                            on = 'id_ent_beg',
                                                            how = 'left')
                    df_ent_assigned = df_ent_assigned.rename(columns = {'id_parag_x':'id_parag_quote', 
                                                                        'id_parag_y':'id_parag_ent'})
                    col_drop_num_cand_1 = ['tam_quote', 'quote_language', 'num_dif_grammar_class', 'num_verb', 'num_noun']
                    df_ent_assigned = df_ent_assigned.drop(columns = col_drop_num_cand_1)
                    df_ent_assigned = df_ent_assigned.rename(columns = {'id_parag_quote':'id_parag'})
                    order_cols_df_ent_assigned = ['id_pair', 'id_parag', 
                                      'id_quote_beg', 'id_quote_end', 
                                      'quote_text', 
                                      'entity', 'entity_upper', 'entity_full_name', 
                                      'id_parag_ent', 'id_ent_beg', 'id_ent_end']
                    df_ent_assigned = df_ent_assigned.reindex(columns = order_cols_df_ent_assigned)
                    df_ent_assigned = df_ent_assigned.drop_duplicates()
                    return df_ent_assigned
                    break
            
                if num_candidates > 1: 
                    df_ent_assigned = closer_ent_from_quote_pair(ent_candidates_try, df_pair_quotes)  
                    df_ent_assigned = df_ent_assigned.drop_duplicates()
                    return df_ent_assigned
                    break    
    


# It depends on 'assign_entity_no_ties'
# It returns a data.frame with:
### id_pair
### id_parag
### id_quote_beg
### id_quote_end
### quote_text
### id_parag_ent
### entity
### entity_upper
### id_ent_beg
### id_ent_end
### single_name_original
### entity_full_name
### gender
### method
@logger.critical
def assign_entity_quote_pron(PAIR, DF_QUOTES_BEG_END, DF_ENTITIES_POSTAG, DF_PRON_QUOTE_DIST):
    ### -- ARGUMENTS -- ###
    #PAIR = 2
    #DF_QUOTES_BEG_END = df_quotes_beg_end 
    #DF_ENTITIES_POSTAG = df_entities_postag
    #DF_PRON_QUOTE_DIST = df_ent_quote_verbs_pron_gender
    
    ### -- FUNCTION -- ###

    # Info about pair of quotes
    df_pair_quotes = DF_PRON_QUOTE_DIST.query('id_pair == ' + str(PAIR)) 

    # quotes paragraph
    parag = df_pair_quotes['id_parag'].drop_duplicates().tolist()
    
    # pronoun
    pronoun = df_pair_quotes['pronoun'].drop_duplicates().tolist()
    
    # gender of quotes pronoun
    gender = df_pair_quotes['gender'].drop_duplicates().tolist()
    
    # Entity candidates are the entities who have the SAME GENDER:
    ent_candidates = DF_ENTITIES_POSTAG.query('gender == ' + str(gender))

    # How many entities were identified at this paragraph:
    ent_candidates_same_parag = ent_candidates.query('id_parag == ' + str(parag))
    
    num_candidates_same_parag = ent_candidates_same_parag.shape[0]
    
    ### If there are entity candidates 
    if num_candidates_same_parag == 1:
        #print('Same paragraph!')
        
        df_ent_assigned = assign_entity_no_ties(DF_PAIR_QUOTES = df_pair_quotes, 
                                                 DF_ENT_CAND = ent_candidates_same_parag)
    
    elif num_candidates_same_parag > 1:
        #print('Same paragraph!')
        
        df_ent_assigned = closer_ent_from_quote_pair(ENT_CANDIDATES = ent_candidates_same_parag, 
                                       DF_PAIR_QUOTES = df_pair_quotes)
    
    elif num_candidates_same_parag == 0:
       # paragraph of Entity candidates before a given paragraph
        ent_candid_before_parag = DF_ENTITIES_POSTAG.loc[DF_ENTITIES_POSTAG['id_parag'] < parag[0]]
        
        if (gender[0] == 'F' or gender[0] == 'M'):
            ## ---  2nd approach --- ##
            # LAST entity from same gender
            same_gen = ent_candid_before_parag.query('gender == ' + str(gender))
            same_gen_parag_bef = same_gen.query('id_parag == ' + str(max(same_gen['id_parag'])))

            num_candidates_same_gen_parag_bef = len(same_gen_parag_bef)

            if num_candidates_same_gen_parag_bef == 1: # NO TIES
                #print('same_gen_parag_bef & num_candidates_parag_bef == 1')
                df_ent_assigned_noties_same_gen_parag_bef = assign_entity_no_ties(DF_PAIR_QUOTES = df_pair_quotes, 
                                                                                  DF_ENT_CAND = same_gen_parag_bef) 

                df_ent_assigned = df_ent_assigned_noties_same_gen_parag_bef


            if num_candidates_same_gen_parag_bef > 1: # TIES
                #print('same_gen_parag_bef & num_candidates_parag_bef > 1')
                df_ent_assigned_disambiguate_parag_bef = closer_ent_from_quote_pair(ENT_CANDIDATES = same_gen_parag_bef, 
                                                                                    DF_PAIR_QUOTES = df_pair_quotes)

                df_ent_assigned = df_ent_assigned_disambiguate_parag_bef 
        else:
            #print(gender[0])
        #if np.isnan(gender[0]):
            ## --- 1st approach --- ##
            # 'bigger' parag before the current INDEPENDENTLY of gender
            bigger_parag_indep_gender = max(ent_candid_before_parag['id_parag'])

            parag_bef = ent_candid_before_parag.query('id_parag == ' + str(bigger_parag_indep_gender))

            num_candidates_parag_bef = len(parag_bef)


            if(num_candidates_parag_bef == 1): # NO TIES
                #print('parag_bef & num_candidates_parag_bef == 1')
                df_ent_assigned_noties_parag_bef = assign_entity_no_ties(DF_PAIR_QUOTES = df_pair_quotes, 
                                                                         DF_ENT_CAND = parag_bef)    

                df_ent_assigned = df_ent_assigned_noties_parag_bef

            if(num_candidates_parag_bef > 1): # TIES
                #print('parag_bef & num_candidates_parag_bef > 1')
                df_ent_assigned_disambiguate_parag_bef = closer_ent_from_quote_pair(ENT_CANDIDATES = parag_bef, 
                                                                                    DF_PAIR_QUOTES = df_pair_quotes)

                df_ent_assigned = df_ent_assigned_disambiguate_parag_bef
        
    return df_ent_assigned
@logger.critical
def assign_entity_quote_pron_far_from_verb(PAIR, DF_ENTITIES_POSTAG, DF_NEAR_QUOTE_PRON):
    ### -- FUNCTION -- ###
    # Info about pair of quotes
    df_pair_quotes = DF_NEAR_QUOTE_PRON.query('id_pair == ' + str(PAIR)) 
    
    # pronoun paragraph
    parag = df_pair_quotes['pron_parag'].drop_duplicates().tolist()
    
    # pronoun
    pronoun = df_pair_quotes['pronoun'].drop_duplicates().tolist()
    
    # gender of quotes pronoun
    gender = df_pair_quotes['gender'].drop_duplicates().tolist()
    
    # In case there is gender associated
    if (gender[0] == 'F' or gender[0] == 'M'):
        
        # Entity candidates are the entities who have the SAME GENDER:
        ent_candidates = DF_ENTITIES_POSTAG.query('gender == ' + str(gender))
    
        # How many entities were identified at this paragraph:
        ent_candidates_same_parag = ent_candidates.query('id_parag == ' + str(parag))
    
        num_candidates_same_parag = len(ent_candidates_same_parag)
        
        if num_candidates_same_parag == 0:
           # paragraph of Entity candidates before a given paragraph
            ent_candid_before_parag = DF_ENTITIES_POSTAG.loc[DF_ENTITIES_POSTAG['id_parag'] < parag[0]]
            
            # LAST entity from same gender
            same_gen = ent_candid_before_parag.query('gender == ' + str(gender))     
            
            # If there is an entity from same gender:
            if same_gen.shape[0] >= 1:
                same_gen_parag_bef = same_gen.query('id_parag == ' + str(max(same_gen['id_parag'])))

                num_candidates_same_gen_parag_bef = len(same_gen_parag_bef)


                if num_candidates_same_gen_parag_bef == 1: # NO TIES
                    #print('same_gen_parag_bef & num_candidates_parag_bef == 1')
                    df_ent_assigned_noties_same_gen_parag_bef = assign_entity_no_ties(DF_PAIR_QUOTES = df_pair_quotes, 
                                                                                      DF_ENT_CAND = same_gen_parag_bef) 


                    df_ent_assigned = df_ent_assigned_noties_same_gen_parag_bef


                if num_candidates_same_gen_parag_bef > 1: # TIES
                    #print('same_gen_parag_bef & num_candidates_parag_bef > 1')
                    df_ent_assigned_disambiguate_parag_bef = closer_ent_from_quote_pair(ENT_CANDIDATES = same_gen_parag_bef, 
                                                                                        DF_PAIR_QUOTES = df_pair_quotes)


                    df_ent_assigned = df_ent_assigned_disambiguate_parag_bef 
                    
            # If there is NO entity from same gender:
            else:
                #print('NO entity from same gender')
                
                dict_ent_assigned = {'id_pair': df_pair_quotes['id_pair'],
                   'id_parag': df_pair_quotes['id_parag'], 
                   'id_quote_beg': df_pair_quotes['id_quote_beg'],
                   'id_quote_end': df_pair_quotes['id_quote_end'],
                   'quote_text': df_pair_quotes['quote_text'],
                   'entity': np.nan,
                   'entity_upper': np.nan, 
                   'entity_full_name': np.nan,
                   'id_parag_ent': np.nan,
                   'id_ent_beg': np.nan,
                   'id_ent_end': np.nan}
    
    
                df_ent_assigned = pd.DataFrame(data = dict_ent_assigned)
            
        ## If there are entity candidates 
        elif num_candidates_same_parag == 1:
            #print('Same paragraph & num_candidates_parag_bef == 1')
            
            df_ent_assigned = assign_entity_no_ties(DF_PAIR_QUOTES = df_pair_quotes, 
                                                     DF_ENT_CAND = ent_candidates_same_parag)
        else: # num_candidates_same_parag > 1:
            #print('Same paragraph & num_candidates_parag_bef > 1')
            
            df_ent_assigned = closer_ent_from_quote_pair(ENT_CANDIDATES = ent_candidates_same_parag, 
                                           DF_PAIR_QUOTES = df_pair_quotes)
            
    # In case there is NO gender associated IT IS NOT POSSIBLE TO MAP TO AN ENTITY       
    else:
        #print('Not possible')
        dict_ent_assigned = {'id_pair': df_pair_quotes['id_pair'],
                   'id_parag': df_pair_quotes['id_parag'], 
                   'id_quote_beg': df_pair_quotes['id_quote_beg'],
                   'id_quote_end': df_pair_quotes['id_quote_end'],
                   'quote_text': df_pair_quotes['quote_text'],
                   'entity': np.nan,
                   'entity_upper': np.nan, 
                   'entity_full_name': np.nan,
                   'id_parag_ent': np.nan,
                   'id_ent_beg': np.nan,
                   'id_ent_end': np.nan}
    
    
        df_ent_assigned = pd.DataFrame(data = dict_ent_assigned)
        
        
    return df_ent_assigned
    
    
    
    
# Assign a quote to an entity based on verbs
# It returns a list with:
### Entities (character)
@logger.critical
def assign_ent_quote_verbs(DF_QUOTES_BEG_END, DF_POSTAG, DF_ALL_ENTS, DF_VERBS):
    #DF_QUOTES_BEG_END = df_quote_verbs  
    #DF_POSTAG = df_postag 
    #DF_ALL_ENTS = df_all_entities 
    #DF_VERBS = verbs_df
        
    DF_VERBS_IDENTIFIED = DF_QUOTES_BEG_END[DF_QUOTES_BEG_END['word_citation'] == 1]

    if DF_VERBS_IDENTIFIED.shape[0] > 0:        
        # Where those verbs were found
        DF_QUOTES_BEG_END['verb_before_quote'] = np.where(DF_QUOTES_BEG_END['id_word'] < DF_QUOTES_BEG_END['id_quote_beg'], 1, 0)        
        DF_QUOTES_BEG_END['verb_after_quote'] = np.where(DF_QUOTES_BEG_END['id_word'] > DF_QUOTES_BEG_END['id_quote_end'], 1, 0)        
        DF_QUOTES_BEG_END['no_citation_verb'] = np.where(DF_QUOTES_BEG_END['verb_before_quote'] == DF_QUOTES_BEG_END['verb_after_quote'], 1, 0)

    else:
        # Where those verbs were found
        DF_QUOTES_BEG_END['verb_before_quote'] = 0        
        DF_QUOTES_BEG_END['verb_after_quote'] = 0  
        DF_QUOTES_BEG_END['no_citation_verb'] = 1
    
    
    list_ent_cand = []
    for INDEX,ROW in DF_QUOTES_BEG_END.iterrows():
        
        id_parag = ROW['id_parag']
        id_quote_begin = ROW['id_quote_beg']
        id_quote_end = ROW['id_quote_end']
                
            
        if ROW['no_citation_verb'] == 1: # | ROW['verb_inside_quote'] == 1:
            list_ent_cand.append(np.nan) 
        else:
            #verb_after_quote
            if ROW['verb_after_quote'] == 1:
                dataset_after_quote = DF_POSTAG[DF_POSTAG['id_word'] > id_quote_end]
                dataset_after_quote_dot = dataset_after_quote[dataset_after_quote['word'] == '.']
                next_dot = min(dataset_after_quote_dot['id_word'])
                sub_dataset = DF_POSTAG.iloc[(id_quote_end + 1):(next_dot + 1)]
                   
                    
            #verb_before_quote       
            elif ROW['verb_before_quote'] == 1:
                dataset_before_quote = DF_POSTAG[DF_POSTAG['id_word'] < id_quote_begin]
                dataset_before_quote_dot = dataset_before_quote[dataset_before_quote['word'] == '.']
                last_dot = max(dataset_before_quote_dot['id_word'])
                sub_dataset = DF_POSTAG.iloc[(last_dot + 1):(id_quote_begin)]
            
            
            # Is there any entity? Join/merge context near verb and the entities itself
            ent_cand = sub_dataset.merge(DF_ALL_ENTS,
                                         left_on = 'word', 
                                         right_on = 'single_name', 
                                         how = 'inner')
            
            if ent_cand.shape[0] == 0:
                list_ent_cand.append(np.nan) 
            else:
                entities_candidates = ent_cand['complete_name'].drop_duplicates()[0]
                list_ent_cand.append(entities_candidates)
                
    return list_ent_cand    
    
    
    
@logger.critical    
def assign_nan_to_all_quotes(DF_QUOTES_BEG_END):
    id_pair = []
    id_parag = []
    id_quote_beg = []
    id_quote_end = []
    quote_text = []
    entity_full_name = []
    id_parag_ent = []
    id_ent_beg = []
    id_ent_end = []

    numRows = DF_QUOTES_BEG_END.shape[0]
        

    for i in range(0, numRows):
        quote_pair = DF_QUOTES_BEG_END.iloc[i]['id_pair']

        id_pair.append(quote_pair)

        id_parag.append(int(DF_QUOTES_BEG_END.iloc[i]['id_parag']))

        id_quote_beg.append(int(DF_QUOTES_BEG_END.iloc[i]['id_quote_beg']))

        id_quote_end.append(int(DF_QUOTES_BEG_END.iloc[i]['id_quote_end']))

        quote_text.append(DF_QUOTES_BEG_END.iloc[i]['quote_text'])

        entity_full_name.append(np.nan)

        id_parag_ent.append(np.nan)

        id_ent_beg.append(np.nan)

        id_ent_end.append(np.nan)



    df = pd.DataFrame(list(zip(id_pair, id_parag, id_quote_beg, id_quote_end, 
                                        quote_text, entity_full_name, #entity,
                                        id_parag_ent, id_ent_beg, id_ent_end)),
                        columns = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 
                                    'quote_text', 'entity_full_name', #'entity', 
                                    'id_parag_ent', 'id_ent_beg', 'id_ent_end'])  
    
    return df            
    
    
    
    
    
    
# Assign a VERB to a QUOTE
# It uses 'recognize_verbs_in_paragraphs'
# It uses 'closer_verb_from_quote_pair'
# It returns a data.frame with:
### id_pair
### id_parag
### id_quote_begin
### id_quote_end
### tam_quote
### quote_text
### quote_language
### num_dif_grammar_class
### num_verb
### num_noun
### id_word
### word
### pos_tag
### gender
### number
### word_upper
### word_citation
@logger.critical
def assign_quote_verbs(DF_QUOTES_BEG_END, LIST_VERBS, PARAGRAPHS, DF_POSTAG, DF_ALL_ENTS):
    #DF_QUOTES_BEG_END = df_quotes_beg_end   
    #LIST_VERBS = VERBS
    #PARAGRAPHS = paragraphs
    #DF_POSTAG = df_postag
    #DF_ALL_ENTS = df_all_entities
    
    
    DF_VERBS_IDENTIFIED = recognize_verbs_in_paragraphs(DF_QUOTES_BEG_END = DF_QUOTES_BEG_END, 
                                                        LIST_VERBS = LIST_VERBS, 
                                                        PARAGRAPHS = PARAGRAPHS)

    # Add verbs positions
    DF_VERBS_IDENTIFIED_POSTAG = DF_POSTAG.merge(DF_VERBS_IDENTIFIED, 
                                                 on = ['id_parag', 'word_upper', 'pos_tag'],
                                                 how = 'left')
        
        
    DF_VERBS_IDENTIFIED_POSTAG = DF_VERBS_IDENTIFIED_POSTAG[DF_VERBS_IDENTIFIED_POSTAG['word_citation'] == 1]

    
    num_VERBS_IDENTIFIED = DF_VERBS_IDENTIFIED.shape[0]
    
    if num_VERBS_IDENTIFIED > 0:
        DF_QUOTES_BEG_END = DF_QUOTES_BEG_END.merge(DF_VERBS_IDENTIFIED_POSTAG,
                                                        on = 'id_parag',  
                                                        how = 'left')
        
        # Number of verbs by quote pair
        # Useful when there are more than a verb to each quote
        num_verbs_by_quote_pair = DF_QUOTES_BEG_END.groupby(by = 'id_pair')['id_pair'].count()
        # Quote pairs that can be associated with more than a verb
        id_pair_need_disamb = num_verbs_by_quote_pair[num_verbs_by_quote_pair > 1].index.tolist()
        
        # Se há empates
        if len(id_pair_need_disamb) > 0:
            # Sub-set dos empates
            need_disamb = DF_QUOTES_BEG_END[DF_QUOTES_BEG_END['id_pair'].isin(id_pair_need_disamb)] 
            # Sub-set SEM empates
            no_need_disamb = DF_QUOTES_BEG_END[~DF_QUOTES_BEG_END["id_pair"].isin(id_pair_need_disamb)]
            
            # Desempatar cada par de aspas com empate
            list_pair_closer = []
            
            for pair_to_disamb in id_pair_need_disamb:
                aux_to_disamb = DF_QUOTES_BEG_END[DF_QUOTES_BEG_END['id_pair'] == pair_to_disamb]
                df_verbs_to_disamb = aux_to_disamb[['id_word', 'word']].drop_duplicates()
                df_pair_quotes_to_disamb = aux_to_disamb[['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text']].drop_duplicates()
        
                # Se há mais de um verbo para um par de aspas: desempatar
                aux = closer_verb_from_quote_pair(df_verbs_to_disamb, df_pair_quotes_to_disamb)
                list_pair_closer.append(aux)

    
            df_pair_closer = pd.concat(list_pair_closer)
        
        
            need_disamb_after_disamb = need_disamb.merge(df_pair_closer, 
                  on = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'id_word', 'word'],
                  how = 'inner')
            
            # Juntar Sub-set dos empates & Sub-set SEM empates
            DF_QUOTES_BEG_END_after_disamb = pd.concat([no_need_disamb, need_disamb_after_disamb], 
                                                       axis = 0)
            DF_QUOTES_BEG_END_after_disamb = DF_QUOTES_BEG_END_after_disamb.sort_values(['id_pair', 'id_parag'], 
                                                                                        ascending = [True, True])
            
            
            return DF_QUOTES_BEG_END_after_disamb
        
        else:         # Se NÃO há empates
            return DF_QUOTES_BEG_END   
    else:
        return 999999  
    
    
    
    
    
# To have context about each entity - NOT BEING USED
@logger.critical
def characterize_entities(INDEX, DF, WINDOW_LENGTH):
    # df_noun_adj_ent at INDEX position
    ind_entity = DF.loc[INDEX]
    
    # What is the gender associated with the name?
    gender_name = ind_entity['gender']
    
    # Neighborhood around the entity 
    row_inf = INDEX - WINDOW_LENGTH
    if row_inf < 0:
        row_inf = 0
    
    num_row_df = DF.shape[0]
    
    row_sup = INDEX + WINDOW_LENGTH + 1
    if row_sup > num_row_df:
        row_sup = num_row_df
    
    
    # Characteristics
    caract_aux = DF.iloc[row_inf:row_sup]
    
    # Entity
    df_ent = caract_aux.loc[INDEX]
    df_ent = df_ent.to_frame()
    df_ent = df_ent.T
    
    
    # Filtering characteristics to remove 'entities'
    caract_aux = caract_aux.drop(INDEX)
    
    
    if isinstance(gender_name, float): # No gender -> We infer it
        # What is the name's gender given the name neighborhood
        caract_masc = caract_aux[caract_aux['gender'].str.contains("M", na = False)]
        caract_fem = caract_aux[caract_aux['gender'].str.contains("F", na = False)]
        
        num_masc = caract_masc.shape[0]
        num_fem = caract_fem.shape[0]
    
        
        if num_masc > num_fem:
            df_ent.loc[INDEX, ['gender']] = 'M'
        elif num_masc < num_fem:
            df_ent.loc[INDEX, ['gender']] = 'F'
        else:
            df_ent.loc[INDEX, ['gender']] = '999999'
            
        df_caract = caract_aux
        bin_error = 0

    elif gender_name == "F" or gender_name == "M":
        # What features agree with the entity's gender?
        df_caract = caract_aux[caract_aux.gender.str.contains(gender_name, na = False)]
        bin_error = 0
    else:
        bin_error = 1
        
        
    # Entity & features
    df_ent_caract = pd.concat([df_ent, df_caract])    
    
    df_ent_caract['index_entity'] = INDEX
    
    
    return [bin_error, df_ent_caract]
    
    

# To have context about each entity based on:
## only Nouns and Adjectives around the entity
## entity gender
# It returns a data.frame with:
### id_ent_beg
### id_ent_end
### gender
### context_before_sent
### context_after_sent
@logger.critical
def characterize_entities_given_gender(INDEX_BEG, INDEX_END, GENDER, DF_POSTAG, WINDOW_LENGTH):
    
    # Neighborhood around the entity 
    row_inf = INDEX_BEG - WINDOW_LENGTH
    if row_inf < 0:
        row_inf = 0
    
    num_row_df = DF_POSTAG.shape[0]
    
    row_sup = INDEX_END + WINDOW_LENGTH + 1
    if row_sup > num_row_df:
        row_sup = num_row_df
    

    # Before entity
    context_before = DF_POSTAG.iloc[row_inf:INDEX_BEG]
    context_before = context_before[context_before['pos_tag'].isin(['NOUN', 'ADJ'])]
    context_before_samegender = context_before[context_before['gender'] == GENDER]

    if context_before_samegender.shape[0] > 0:
        context_before_sent = " ".join(context_before_samegender['word']) 
    else:
        context_before_sent = np.nan
    
    # After entity
    context_after = DF_POSTAG.iloc[(INDEX_END + 1):row_sup]
    context_after = context_after[context_after['pos_tag'].isin(['NOUN', 'ADJ'])]
    context_after_samegender = context_after[context_after['gender'] == GENDER]

    if context_after_samegender.shape[0] > 0:
        context_after_sent = " ".join(context_after_samegender['word']) 
    else:
        context_after_sent = np.nan
        
    
    # Object to return
    dict_return = {'id_ent_beg': [INDEX_BEG],
                   'id_ent_end': [INDEX_END], 
                   'gender': [GENDER],
                   'context_before_sent': [context_before_sent],
                   'context_after_sent': [context_after_sent]}
    
    df_return = pd.DataFrame(data = dict_return)
        
        
    return df_return    
    
    
    
    
    
# To have context about each entity based on Nouns and Adjectives around the entity AND infer entity gender
# It returns a data.frame with:
### id_ent_beg
### id_ent_end
### gender
### context_before_sent
### context_after_sent
@logger.critical
def characterize_entities_infer_gender(INDEX_BEG, INDEX_END, DF_POSTAG, WINDOW_LENGTH):
    
    # Neighborhood around the entity 
    row_inf = INDEX_BEG - WINDOW_LENGTH
    if row_inf < 0:
        row_inf = 0
    
    num_row_df = DF_POSTAG.shape[0]
    
    row_sup = INDEX_END + WINDOW_LENGTH + 1
    if row_sup > num_row_df:
        row_sup = num_row_df
    

    # Before entity
    context_before = DF_POSTAG.iloc[row_inf:INDEX_BEG]
    context_before = context_before[context_before['pos_tag'].isin(['NOUN', 'ADJ'])]
    
    if context_before.shape[0] > 0:
        context_before_sent = " ".join(context_before['word']) 
    else:
        context_before_sent = np.nan
    
    caract_masc = context_before[context_before['gender'] == 'M']
    caract_fem = context_before[context_before['gender'] == 'F']
        
    num_masc = caract_masc.shape[0]
    num_fem = caract_fem.shape[0]
    
    if num_masc > num_fem:
        GENDER_BEF = 'M'
    elif num_masc < num_fem:
        GENDER_BEF = 'F'
    else:
        GENDER_BEF = 'Undefined'
    
    # After entity
    context_after = DF_POSTAG.iloc[(INDEX_END + 1):row_sup]
    context_after = context_after[context_after['pos_tag'].isin(['NOUN', 'ADJ'])]

    
    if context_after.shape[0] > 0:
        context_after_sent = " ".join(context_after['word']) 
    else:
        context_after_sent = np.nan
    
    
    caract_masc = context_after[context_after['gender'] == 'M']
    caract_fem = context_after[context_after['gender'] == 'F']
        
    num_masc = caract_masc.shape[0]
    num_fem = caract_fem.shape[0]
    
    if num_masc > num_fem:
        GENDER_AFTER = 'M'
    elif num_masc < num_fem:
        GENDER_AFTER = 'F'
    else:
        GENDER_AFTER = 'Undefined'
        
    
    # Final gender
    if GENDER_BEF == GENDER_AFTER:
        GENDER = GENDER_BEF
    elif GENDER_BEF == 'Undefined' and GENDER_AFTER == 'Undefined':
        GENDER = 'Undefined' 
    elif (GENDER_BEF == 'M' and GENDER_AFTER == 'F') or (GENDER_BEF == 'F' and GENDER_AFTER == 'M'):
        GENDER = 'Undefined'  
    elif GENDER_BEF == 'Undefined' and (GENDER_AFTER == 'M' or GENDER_AFTER == 'F'):
        GENDER = GENDER_AFTER 
    elif (GENDER_BEF == 'M' or GENDER_BEF == 'F') and GENDER_AFTER == 'Undefined':
        GENDER = GENDER_BEF  
    else:
        GENDER = np.nan()
        
    
    dict_return = {'id_ent_beg': [INDEX_BEG],
                   'id_ent_end': [INDEX_END], 
                   #'gender_bef': [GENDER_BEF],
                   #'gender_aft': [GENDER_AFTER],
                   'gender': [GENDER],
                   'context_before_sent': [context_before_sent],
                   'context_after_sent': [context_after_sent]}
    
    df_return = pd.DataFrame(data = dict_return)
        
        
    return df_return    
    
    


# What is the closest entity to a quotation mark?
# It uses 'dif_pair_idquote_ident'
# It returns:
## a dataframe
@logger.critical
def closer_ent_from_quote_pair(ENT_CANDIDATES, DF_PAIR_QUOTES):

    # Indexes
    index_quote_beg = DF_PAIR_QUOTES["id_quote_beg"].values.tolist()
    index_quote_end = DF_PAIR_QUOTES["id_quote_end"].values.tolist()
    index_ent = ENT_CANDIDATES["id_ent_beg"].values.tolist()

    
    # Quote beggining
    beg = dif_pair_idquote_ident(ID_QUOTE = index_quote_beg, ID_ENT = index_ent)
    beg = beg.rename(columns = {'id_quote': 'id_quote_beg', 'dif':'dif_beg', 'dif_abs':'dif_abs_beg'})

    pair_beg = DF_PAIR_QUOTES[['id_pair', 'id_parag', 'id_quote_beg', 'quote_text']]
    beg = beg.merge(pair_beg,
                   on = 'id_quote_beg',
                   how = 'left')
    
    # Quote end
    end = dif_pair_idquote_ident(ID_QUOTE = index_quote_end, ID_ENT = index_ent)
    end = end.rename(columns = {'id_quote': 'id_quote_end', 'dif':'dif_end', 'dif_abs':'dif_abs_end'})

    pair_end = DF_PAIR_QUOTES[['id_pair', 'id_parag', 'id_quote_end']]
    end = end.merge(pair_end,
                   on = 'id_quote_end',
                   how = 'left')

    
    # Join/Merge 'beg' and 'end'
    beg_end = beg.merge(end,
                  on = ['id_pair', 'id_parag', 'entity'],
                  how = 'outer')
    beg_end = beg_end.reindex(columns = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text', 'entity', 'dif_beg', 'dif_end', 'dif_abs_beg', 'dif_abs_end'])
    beg_end = beg_end.sort_values(['id_pair', 'entity'], ascending = [True, True]) 
    
    
    # Long format
    beg_end_long = beg_end.melt(id_vars = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text', 'entity'], 
                                value_vars = ['dif_abs_beg', 'dif_abs_end'],
                                value_name = 'dist') 
    beg_end_long = beg_end_long.sort_values('dist', ascending = True)
    
    
    # Closer entities (it can be more than one, in case of ties)
    closer = beg_end_long[beg_end_long['dist'] == min(beg_end_long['dist'])]
    
    
    # Join with entities name
    closer = closer.merge(ENT_CANDIDATES, 
                          left_on = 'entity',
                          right_on = 'id_ent_beg',
                          how = "left")
    closer = closer.drop(columns = ['variable', 'dist', 'entity_x'])
    closer = closer.rename(columns = {'id_parag_x':'id_parag', 
                                      'id_parag_y':'id_parag_ent', 
                                      'entity_y':'entity', 
                                      'word_upper':'ent_upper'})
    # Reorder columns
    order_cols_closer = ['id_pair', 'id_parag', 
                         'id_quote_beg', 'id_quote_end', 
                         'quote_text', 
                         'entity', 'entity_upper', 'entity_full_name', 
                         'id_parag_ent',
                         'id_ent_beg', 'id_ent_end']
    
    
    closer = closer.reindex(columns = order_cols_closer)
    
    
    closer = closer.drop_duplicates()
    
    return closer   
    
    
    
    
# What is the closest verb to a quotation 
# It uses 'dif_pair_idquote_ident'
# It returns:
## a dataframe
@logger.critical
def closer_verb_from_quote_pair(VERB_CANDIDATES, DF_PAIR_QUOTES):

    # Indexes
    index_quote_beg = DF_PAIR_QUOTES["id_quote_beg"].values.tolist()
    index_quote_end = DF_PAIR_QUOTES["id_quote_end"].values.tolist()
    index_verb = VERB_CANDIDATES["id_word"].values.tolist()

    
    # Quote beggining
    beg = dif_pair_idquote_ident(ID_QUOTE = index_quote_beg, ID_ENT = index_verb)
    beg = beg.rename(columns = {'id_quote':'id_quote_beg', 'dif':'dif_beg', 'dif_abs':'dif_abs_beg', 'entity':'word'})

    pair_beg = DF_PAIR_QUOTES[['id_pair', 'id_parag', 'id_quote_beg', 'quote_text']]
    beg = beg.merge(pair_beg,
                   on = 'id_quote_beg',
                   how = 'left')
    
    # Quote end
    end = dif_pair_idquote_ident(ID_QUOTE = index_quote_end, ID_ENT = index_verb)
    end = end.rename(columns = {'id_quote': 'id_quote_end', 'dif':'dif_end', 'dif_abs':'dif_abs_end', 'entity':'word'})

    pair_end = DF_PAIR_QUOTES[['id_pair', 'id_parag', 'id_quote_end']]
    end = end.merge(pair_end,
                   on = 'id_quote_end',
                   how = 'left')
    

    # Join/Merge 'beg' and 'end'
    beg_end = beg.merge(end,
                  on = ['id_pair', 'id_parag', 'word'],
                  how = 'outer')
    beg_end = beg_end.reindex(columns = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text', 'word', 'dif_beg', 'dif_end', 'dif_abs_beg', 'dif_abs_end'])
    beg_end = beg_end.sort_values(['id_pair', 'word'], ascending = [True, True]) 
    
    
    # Long format
    beg_end_long = beg_end.melt(id_vars = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text', 'word'], 
                                value_vars = ['dif_abs_beg', 'dif_abs_end'],
                                value_name = 'dist') 
    beg_end_long = beg_end_long.sort_values('dist', ascending = True)

    # Closer entities (it can be more than one, in case of ties)
    closer = beg_end_long[beg_end_long['dist'] == min(beg_end_long['dist'])]
    
    # Join with entities name
    closer = closer.merge(VERB_CANDIDATES, 
                          left_on = 'word',
                          right_on = 'id_word',
                          how = "left")

    closer = closer.drop(columns = ['variable', 'dist', 'word_x', 'quote_text'])
    closer = closer.rename(columns = {'word_y':'word'})
    
    return closer    
    
    
    
# It returns '1' if an entity is inside a quote
@logger.critical
def define_entity_inside_quote(row):
    if row['id_ent_beg'] >= row ['id_quote_beg']:
        if row['id_ent_end'] <= row ['id_quote_end']:
            return 1
        else:
            return 0
    else:
        return 0    
        
        
@logger.critical
def define_len_entity_intersec(row):
    return len(row['entity_intersec'].split(" "))        
    
    
@logger.critical 
def define_odds_even(row):
     return row['num_quotes_by_parag'] % 2   

# It returns 0 or 1
@logger.critical
def define_pron_inside_quote(row):
    if ((row['id_word'] >= row['id_quote_beg']) and (row['id_word'] <= row['id_quote_end'])):
        return 1      
    else:
        return 0 
    
    

# It needs: 
### define_len_entity
### list_to_dataframe
# If models identify entity names separately we must concatenate them
# It returns a data.frame with same columns from DF_ENTITIES_POSTAG:
### id_parag
### entity
### entity_upper
### id_ent_beg
### id_ent_end
@logger.critical
def concat_consecutive_entities(DF_ENTITIES_POSTAG):
    
    DF_ENTITIES_POSTAG_aux = DF_ENTITIES_POSTAG

    # Remove index
    DF_ENTITIES_POSTAG_aux = DF_ENTITIES_POSTAG_aux.reset_index(drop = True)

    numrows = DF_ENTITIES_POSTAG_aux.shape[0] - 1
    
    for i in range(0, numrows):
    
        ent_1 = DF_ENTITIES_POSTAG_aux.loc[i]
        ent_2 = DF_ENTITIES_POSTAG_aux.loc[i+1]

        dif = ent_2['id_ent_beg'] - ent_1['id_ent_end']

        if dif == 1:
            entity_updated = ent_1['entity'] + ' ' + ent_2['entity']
            entity_upper_updated = ent_1['entity_upper'] + ' ' + ent_2['entity_upper']
            
            DF_ENTITIES_POSTAG_aux.at[i,'entity'] = entity_updated
            DF_ENTITIES_POSTAG_aux.at[i,'entity_upper'] = entity_upper_updated
            DF_ENTITIES_POSTAG_aux.at[i,'id_ent_end'] = ent_2['id_ent_end'] 


            DF_ENTITIES_POSTAG_aux.at[i + 1,'entity'] = entity_updated
            DF_ENTITIES_POSTAG_aux.at[i + 1,'entity_upper'] = entity_upper_updated
            DF_ENTITIES_POSTAG_aux.at[i + 1,'id_ent_beg'] = ent_1['id_ent_beg'] 
            
            
    
    DF_ENTITIES_POSTAG_aux['len_entity'] = DF_ENTITIES_POSTAG_aux.apply(lambda row: define_len_entity(row), axis = 1)

    ## -- If a complete name is composed by more than 2 names: we will keep the biggest version of the name
    
    # Remove duplicated entries
    DF_ENTITIES_POSTAG_aux = DF_ENTITIES_POSTAG_aux.drop_duplicates()
    
    id_ent_beg_list = DF_ENTITIES_POSTAG_aux['id_ent_beg'].drop_duplicates().tolist()

    list_filter_max_len_entity = []

    for id_ent_beg in id_ent_beg_list:
        sub_dataset = DF_ENTITIES_POSTAG_aux[DF_ENTITIES_POSTAG_aux['id_ent_beg'] == id_ent_beg]
    
        num_row_sub_dataset = sub_dataset.shape[0]
    
        if num_row_sub_dataset == 1:
            list_filter_max_len_entity.append(sub_dataset)
    
        if num_row_sub_dataset > 1:
            max_len_entity = max(sub_dataset['len_entity'])
            sub_dataset_max_len_entity = sub_dataset[sub_dataset['len_entity'] == max_len_entity]
            list_filter_max_len_entity.append(sub_dataset_max_len_entity)
        
        
    df_entities_postag_filter_max_len_entity = list_to_dataframe(list_filter_max_len_entity)
    
    return df_entities_postag_filter_max_len_entity 
    
    
    
    


# To return the index of the list that is not empty
# It is used at 'text_in_doublequotes'
@logger.critical
def condition_x_notempty(X): return X != '' 




# It returns an integer
@logger.critical
def count_consecutive_entities(DF_ENTITIES_POSTAG):
    COUNT = 0
    
    DF_ENTITIES_POSTAG_aux = DF_ENTITIES_POSTAG

    # Remove index
    DF_ENTITIES_POSTAG_aux = DF_ENTITIES_POSTAG_aux.reset_index(drop = True)
    
    numrows = DF_ENTITIES_POSTAG_aux.shape[0] - 1
    
    for i in range(0, numrows):
    
        ent_1 = DF_ENTITIES_POSTAG_aux.loc[i]
        ent_2 = DF_ENTITIES_POSTAG_aux.loc[i+1]

        dif = ent_2['id_ent_beg'] - ent_1['id_ent_end']

        if dif == 1:
            COUNT = COUNT + 1
            
    return COUNT



# to create a data frame by LIST with ARTICLEID as column
@logger.critical
def create_df(ARTICLEID, LEN):
    var = [ARTICLEID] * LEN
    df = pd.DataFrame(list(var), columns = ['articleId'])
    return df 
    
    
    
# Add a column/variable that represents final entity
# It returns a character
@logger.critical
def define_entity_paragraph(row):
    if pd.isna(row['ent_cand']):
        return np.nan      
    else:
        return row['id_parag']    
    
    
    
# Add a column/variable that represents final entity
# It returns a character
@logger.critical
def define_final_entity(row):
    if pd.isna(row['entity_intersec']):
        return row['entity_orig']      
    else:
        return row['entity_intersec']  
        
        
@logger.critical 
def define_len_entity(row):
    return row['id_ent_end'] - row['id_ent_beg'] + 1
      



# Difference (in absolute value) between each pair of sentence indexes
@logger.critical
def dif_pair(pair): return abs(pair[0] - pair[1])




# It uses 'dif_pair'
# It returns:
## a dataframe with:
### id_quote: position of the quotation mark 
### entity:   position of the entity
### dif:      difference between 'id_quote' and 'entity'
### dif_abs:  difference between 'id_quote' and 'entity', in absolute value
@logger.critical
def dif_pair_idquote_ident(ID_QUOTE, ID_ENT):
    # All possible pair combination of 'sentence with quotation index' and 'sentence with entity index'
    pair_idquote_ident = [(x, y) for x in ID_QUOTE for y in ID_ENT]  
 
    
    # Convert 'pair_idquote_ident' into numpy array
    pair_idquote_ident_array = np.asarray(pair_idquote_ident)


    # Difference (in absolute value) between each pair of sentence indexes
    dif_pair_idquote_ident = [dif_pair(pair) for pair in pair_idquote_ident] 
    
    
    # 'cbind' quote pairs, entities difference between them
    dif_pair_idquote_ident_dif_array = np.column_stack((pair_idquote_ident_array, 
                                                        dif_pair_idquote_ident))


    # Convert 'dif_pair_idquote_ident_dif_array' into a LONG FORMAT data.frame
    dif_pair_idquote_ident_dif_df = pd.DataFrame(dif_pair_idquote_ident_dif_array, 
                                             columns = ['id_quote', 'entity', 'dif'])

    # Absolute distance
    dif_pair_idquote_ident_dif_df['dif_abs'] = abs(dif_pair_idquote_ident_dif_df['dif'])
        
    return dif_pair_idquote_ident_dif_df




# It returns a distance matrix between the quote's paragraphs and the entity's paragraphs.
# It needs: dif_pair
@logger.critical
def distance_quote_entities(INDEX_PARAG_QUOTE, INDEX_ENT):
    # All possible pair combination of 'sentence with quotation index' and 'sentence with entity index'
    pair_idquote_ident = [(x, y) for x in INDEX_PARAG_QUOTE for y in INDEX_ENT]   
    # Convert 'pair_idquote_ident' into numpy array
    pair_idquote_ident_array = np.asarray(pair_idquote_ident)
    
    # Difference (in absolute value) between each pair of sentence indexes
    dif_pair_idquote_ident = [dif_pair(pair) for pair in pair_idquote_ident]  
    # Convert 'dif_pair_idquote_ident' into numpy array
    dif_pair_idquote_ident_array = np.array(dif_pair_idquote_ident)

    # 'cbind' pair_idquote_ident_array and dif_pair_idquote_ident_array
    dif_pair_idquote_ident_dif_array = np.column_stack((pair_idquote_ident_array, 
                                                        dif_pair_idquote_ident_array))

    # Convert dif_pair_idquote_ident_dif_array into a long format data.frame
    dif_pair_idquote_ident_df = pd.DataFrame(dif_pair_idquote_ident_dif_array, 
                                             columns = ['quote', 'entity', 'dif'])

    # Pivot long format object to wide format
    dif_pair_idquote_ident_df_pv = dif_pair_idquote_ident_df.pivot(index = 'quote', columns = 'entity', values = 'dif')


    # Column index associated with the minimum value by row 
    pos = dif_pair_idquote_ident_df_pv.apply(np.argmin, axis = 'columns')

    indices_to_access = list(dif_pair_idquote_ident_df_pv.columns[pos])
    d = {'parag_id_quote': dif_pair_idquote_ident_df_pv.index, 
         'entity_index': indices_to_access}

    df_quote_near_ent = pd.DataFrame(data = d)
    
    return df_quote_near_ent    
    

   





# Entities on a data.frame 
# Input:
# ENTITIES as a list
# Output:
### id_parag: paragraph index 
### entity: name itself
### first_name: only first name in capital letters
### family_name: only family name in capital letters
@logger.critical
def entities_dataframe(ENTITIES):
    df_ent = pd.DataFrame(ENTITIES)
    
    df_ent = df_ent.rename(columns = {0:'id_parag', 1:'entity'})

    # To remove words that are all in capital letter
    df_ent = df_ent[df_ent['entity'].str.match("^[A-Z]*$") == False]

    # To remove words that are all in capital letter hyphen and capital letter
    df_ent = df_ent[df_ent['entity'].str.match("[A-Z]{2}(-?)[A-Z]{2}") == False]

    # Split name in 2	
    df_ent[['first_name', 'family_name']] = df_ent['entity'].str.split(' ', 1, expand = True)

    # Names in Capital letter
    df_ent['first_name'] = df_ent['first_name'].str.upper()
    df_ent['family_name'] = df_ent['family_name'].str.upper()

    # Remove accents from the names
    df_ent['first_name'] = remove_accents(df_ent['first_name']) 
    df_ent['family_name'] = remove_accents(df_ent['family_name'])

        
    return df_ent
    
    
    
# It needs: remove_accents
# It returns a data.frame with:
## id_parag:     paragraph number
## entity:       entity (proper name) with no accents
## entity_upper: entity in uppercase with no accents
## id_ent_beg:   position of the entity begin
## id_ent_end:   position of the entity end
@logger.critical
def entities_postag_format(DF_POSTAG, DF_ENTITIES): 
    #DF_POSTAG = df_postag
    #DF_ENTITIES = df_entities

    # Names in Capital letter to merge
    DF_POSTAG['word_upper'] = DF_POSTAG['word'].str.upper()
    
    # Remove accents from the names in Capital letter to merge
    DF_POSTAG['word_upper'] = remove_accents(DF_POSTAG['word_upper'])
    
    # Remove accents from the names in Capital letter to merge
    DF_ENTITIES['entity_original'] = remove_accents(DF_ENTITIES['entity_original'])
    
    # list with all paragraphs
    all_parag_with_ent = DF_ENTITIES['id_parag'].drop_duplicates()
    
    ls_dict_ent_pos = []
    
    for PARAG_ in all_parag_with_ent:
        #PARAG_ = 3
        
        df_entities_by_parag = DF_ENTITIES.query('id_parag == ' + str(PARAG_))
        df_postag_by_parag = DF_POSTAG.query('id_parag == ' + str(PARAG_))
        df_postag_by_parag = df_postag_by_parag.drop(columns = ['word', 'pos_tag', 'gender', 'number'])
        df_postag_by_parag_aux = df_postag_by_parag

        
        ls_entities = df_entities_by_parag['entity_original'].values.tolist()
        
        
        for ENTITY in ls_entities:
            #ENTITY = ls_entities[0]
            
            # Split entity by " "
            ENTITY_UPPER = ENTITY.upper()
            ENTITY_SPLIT = ENTITY_UPPER.split(' ')
            LEN_ENTITY_SPLIT = len(ENTITY_SPLIT)
            
            # We iterate through 'df_postag_by_parag' to find the position where the name occured
            for INDEX,ROW in df_postag_by_parag.iterrows():
                #INDEX = 9
                #ROW = df_postag_by_parag.iloc[INDEX]
                first_name = ENTITY_SPLIT[0]
                last_name = ENTITY_SPLIT[LEN_ENTITY_SPLIT-1]   
                
                if ROW['word_upper'] == first_name:                    
                    ID_ENT_BEG = ROW['id_word']
                    
                    if LEN_ENTITY_SPLIT == 1:    
                        ID_ENT_END = ID_ENT_BEG
                    if LEN_ENTITY_SPLIT > 1:    
                        if df_postag_by_parag_aux.iloc[INDEX + LEN_ENTITY_SPLIT - 1]['word_upper'] == last_name:
                            ID_ENT_END = df_postag_by_parag_aux.iloc[INDEX + LEN_ENTITY_SPLIT - 1]['id_word']
                    
                    dict_ent_pos = {'id_parag': PARAG_,
                                    'entity': ENTITY,
                                    'entity_upper': ENTITY_UPPER,
                                    'id_ent_beg': ID_ENT_BEG,
                                    'id_ent_end': ID_ENT_END}
                    ls_dict_ent_pos.append(dict_ent_pos)   
            
    # Dataframe format
    df_entities_postag = pd.DataFrame(ls_dict_ent_pos) 
    
    # Re-order
    df_entities_postag = df_entities_postag.sort_values(['id_ent_beg'], ascending = [True]) 
    
    # Remove duplicated entries
    df_entities_postag = df_entities_postag.drop_duplicates()
    
    
    # Check if there are entities as part of other entities BY ITS POSITION

    id_ent_beg_duplicated = df_entities_postag.groupby(['id_ent_beg'])['id_ent_beg'].transform('count')

    if sum(id_ent_beg_duplicated > 1):
        list_ent_beg = list(df_entities_postag['id_ent_beg'].drop_duplicates())
        rebuild = []

        for ent_beg in list_ent_beg: 
            aux_beg = df_entities_postag[df_entities_postag['id_ent_beg'] == ent_beg]

            if aux_beg.shape[0] == 1:
                rebuild.append(aux_beg)    

            if aux_beg.shape[0] == 2:
                ref = aux_beg.iloc[:1, :]
                remain = aux_beg.iloc[1:, :]
                ref_id_ent_end = int(ref['id_ent_end'])
                rem_id_ent_end = int(remain['id_ent_end'])

                if ref_id_ent_end > rem_id_ent_end:
                    rebuild.append(ref)
                if ref_id_ent_end < rem_id_ent_end:
                    rebuild.append(remain)


        df_entities_postag_rebuild = list_to_dataframe(rebuild)
        del df_entities_postag
        df_entities_postag = df_entities_postag_rebuild
        
        
        
    id_ent_end_duplicated = df_entities_postag.groupby(['id_ent_end'])['id_ent_end'].transform('count')

    if sum(id_ent_end_duplicated > 1):
        list_ent_end = list(df_entities_postag['id_ent_end'].drop_duplicates())
        rebuild = []

        for ent_end in list_ent_end: 
            aux_end = df_entities_postag[df_entities_postag['id_ent_end'] == ent_end]

            if aux_end.shape[0] == 1:
                rebuild.append(aux_end)  

            if aux_end.shape[0] == 2:
                ref = aux_end.iloc[:1, :]
                remain = aux_end.iloc[1:, :]
                ref_id_ent_beg = int(ref['id_ent_beg'])
                rem_id_ent_beg = int(remain['id_ent_beg'])

                if ref_id_ent_beg < rem_id_ent_beg:
                    rebuild.append(ref)
                if ref_id_ent_beg > rem_id_ent_beg:
                    rebuild.append(remain)

        df_entities_postag_rebuild = list_to_dataframe(rebuild)
        del df_entities_postag
        df_entities_postag = df_entities_postag_rebuild    
 
    
    return df_entities_postag    
    
    
    
# Add a column/variable to make the difference between quote paragraph and entity paragraph
@logger.critical
def ent_quote_dif_parag(row):
    return row['id_parag'] - row['id_parag_ent'] 



# Add a column/variable to say if quote and entity are in the same paragraph
@logger.critical
def ent_quote_same_parag(row):
    if row['id_parag'] == row['id_parag_ent']:
        return 1
    elif row['id_parag'] > row['id_parag_ent']:
        return 0
    else:
        return 999999    
    
    
    
    
# As we have two entity sets: SPACY and HUGGING FACE - NOT BEING USED NOW
# Let's put all together removing duplicates
# It returns a data.frame with:
### id_parag
### entity
### first_name
### family_name
### first_name_original
### entity_original
### entity_original_upper
#### It needs:
#### ls_entities_as_dataframe
@logger.critical
def ent_spacy_ent_hugface_together_nodup(LS_ENTITIES_SPACY, LS_ENTITIES_HUG_FACE):

    # 'ls_entities_spacy' and 'list_ent_hug_face' together
    ls_entities_dup = LS_ENTITIES_SPACY

    # merge list using for loop and append function
    for ent in LS_ENTITIES_HUG_FACE : 
        ls_entities_dup.append(ent)  

    # Remove duplicated entries
    ls_entities = set(ls_entities_dup)
    
    # Entities as a data.frame
    df_entities = ls_entities_as_dataframe(ls_entities)
    return df_entities    
    
    
# To identify when a name is part of another name
# If this is the case, in the next setp we replace it by full/complete name
# It needs:
### define_len_entity_intersec
### list_to_dataframe
# It returns a data.frame with:
### complete_name
### entity_intersec
@logger.critical
def identify_name_part_another_name(ALL_ENTITIES):

    # Unique/distinct entities
    unique_entities = list(dict.fromkeys(ALL_ENTITIES))
    list_i = []
    list_j = []
    intersec = []
    ent_i_split = []
    ent_j_split = []


    for i in unique_entities:
        for j in unique_entities:
            list_i.append(i)
            entisplit = i.split(" ")
            ent_i_split.append(len(entisplit))
            list_j.append(j)
            entjsplit = j.split(" ")
            ent_j_split.append(len(entjsplit))

            if i in j:
                intersec.append(1)
            else:
                intersec.append(0)

    d = {'list_i': list_i,
         'len_name_i': ent_i_split,
         'list_j': list_j,
         'len_name_j': ent_j_split,
         'intersec': intersec}
    df_intersec = pd.DataFrame(data = d)

    # Cases where the names have an intersection
    df_intersec = df_intersec[df_intersec['intersec'] == 1]

    # Remove cases where the name is being compared with itself 
    df_intersec = df_intersec[df_intersec['list_i'] != df_intersec['list_j']]

    ## Auxiliary objects
    # When the longest name is 'j'
    aux_j_gt_i = df_intersec[df_intersec['len_name_j'] > df_intersec['len_name_i']]
    aux_j_gt_i = aux_j_gt_i.rename(columns = {'list_i':'complete_name', 'list_j':'entity_intersec'})
    aux_j_gt_i = aux_j_gt_i.drop(columns = ['len_name_i', 'len_name_j', 'intersec'])

    # When the longest name is 'i'
    aux_i_gt_j = df_intersec[df_intersec['len_name_j'] < df_intersec['len_name_i']]
    aux_i_gt_j = aux_i_gt_j.rename(columns = {'list_j':'complete_name', 'list_i':'entity_intersec'})
    aux_i_gt_j = aux_i_gt_j.drop(columns = ['len_name_i', 'len_name_j', 'intersec'])

    df_intersec = pd.concat([aux_j_gt_i, aux_i_gt_j])
    
    numrow_df_intersec = df_intersec.shape[0]
    
    if numrow_df_intersec >= 1:
        ## -- To filter the entries with the longest complete name. -- ##

        # We count the length of 'complete_name'
        df_intersec['len_entity_intersec'] = df_intersec.apply(lambda row: define_len_entity_intersec(row), axis = 1)

        # All distinct names
        names = df_intersec['complete_name'].drop_duplicates()

        list_intersec = []

        for name in names:
            subdf_intersec = df_intersec[df_intersec['complete_name'] == name]

            numrow_subdf_intersec = subdf_intersec.shape[0]

            if numrow_subdf_intersec > 1:
                max_subdf_intersec = max(subdf_intersec['len_entity_intersec'])

                subdf_intersec_maxlen_entity_intersec = subdf_intersec[subdf_intersec['len_entity_intersec'] == max_subdf_intersec]

                list_intersec.append(subdf_intersec_maxlen_entity_intersec)

            if numrow_subdf_intersec == 1:
                list_intersec.append(subdf_intersec)


        df_intersec_updated = list_to_dataframe(list_intersec)

        df_intersec_updated = df_intersec_updated.drop(columns = 'len_entity_intersec')    
        
        return df_intersec_updated
    
    if numrow_df_intersec == 0:
        
        return df_intersec    
    
    
@logger.critical
def list_to_dataframe(LIST):
    len_list = len(LIST)
    if len_list >= 1:
        df = LIST[0].reset_index(drop = True)
    
        for part_of_list in range(1, len_list):
            df2 = LIST[part_of_list].reset_index(drop = True)
            
            df = pd.concat([df, df2],           # Rbind DataFrames
                           ignore_index = True,
                           sort = False)
        
    return df   
    
    
    
    
# It is useful when there are entities that are cited only by family name.
# In this case, we replace the family name by first and family name.
# It is useful later on to get the gender of these entities since IBGE dataset uses first name (obviously).
# Input
## DF_ENTITIES dataframe:
### 
# Output: 
## df_rebuild dataframe
### index: artificial index created to organize dataframe
### id_parag: paragraph index 
### entity: name itself
### first_name: only first name in capital letters
### family_name: only family name in capital letters
### first_name_original: only first name in capital letters as originally
@logger.critical
def lookfor_firstname_in_familyname(DF_ENTITIES):
    # To re-order columns
    order_cols_df_rebuild = ['index', 'id_parag', 'entity', 'first_name', 'family_name', 'first_name_original']

    # Add index column
    DF_ENTITIES = DF_ENTITIES.reset_index()
    
    # Add first_name_original column
    DF_ENTITIES['first_name_original'] = DF_ENTITIES['first_name']
    
    # Subset of entities with family name
    have_family_name = DF_ENTITIES[DF_ENTITIES['family_name'].notnull()]
    
    # Subset of entities with no family name
    no_family_name = DF_ENTITIES[DF_ENTITIES['family_name'].isnull()]
    no_family_name = no_family_name.drop(columns = ['family_name']) 
    
    # Subset of entities with FULL name
    full_name_ref = have_family_name.drop(columns = ['id_parag', 'index', 'entity', 'first_name_original'])
    full_name_ref = full_name_ref.drop_duplicates()
    full_name_ref = full_name_ref.rename(columns = {"first_name": "first_name_suggested"})

    # Join: no_family_name & full_name_ref
    # This is useful when the entity is cited by the no_family_name, only
    no_family_name = no_family_name.merge(full_name_ref, 
                                          left_on = 'first_name',   # no_family_name
                                          right_on = 'family_name', # full_name_ref
                                          how = 'left')

    
    # no_family_name with first_name_suggested
    no_family_name_with_sugg = no_family_name[no_family_name['first_name_suggested'].notnull()]
    # first_name_suggested replaces first_name
    no_family_name_with_sugg = no_family_name_with_sugg.drop(columns = ['first_name'])
    no_family_name_with_sugg = no_family_name_with_sugg.rename(columns = {"first_name_suggested": "first_name"})

    # no_family_name at all
    no_family_name_still = no_family_name[no_family_name['first_name_suggested'].isnull()]
    no_family_name_still = no_family_name_still.drop(columns = ['first_name_suggested'])
    
    # Join: no_family_name_still & full_name_ref by 'first_name'
    # This is useful when the entity is cited by the first_name, only
    no_family_name_still = no_family_name_still.merge(full_name_ref, 
                                          left_on = 'first_name',   # no_family_name
                                          right_on = 'first_name_suggested', # full_name_ref
                                          how = 'left')
    
    # first_name_suggested replaces first_name
    no_family_name_still_with_sugg = no_family_name_still.drop(columns = ['first_name', 'family_name_x'])
    no_family_name_still_with_sugg = no_family_name_still_with_sugg.rename(columns = {'first_name_suggested': 'first_name', 'family_name_y': 'family_name'})

    
    # All subsets together
    have_family_name = have_family_name.reindex(columns = order_cols_df_rebuild)
    no_family_name_with_sugg = no_family_name_with_sugg.reindex(columns = order_cols_df_rebuild)
    no_family_name_still_with_sugg = no_family_name_still_with_sugg.reindex(columns = order_cols_df_rebuild)

    
    df_rebuild = pd.concat([have_family_name, 
                            no_family_name_with_sugg, 
                            no_family_name_still_with_sugg], ignore_index = True)
    df_rebuild = df_rebuild.sort_values(['index', 'id_parag'], ascending = [True, True])

    # Dealing with index
    df_rebuild = df_rebuild.set_index('index')

    df_rebuild = df_rebuild.drop_duplicates()    
    

    return df_rebuild  
    
    
    
# ls_entities list as a data frame 
## It depends on: remove_accents
## It returns a data.frame with variables:
### id_parag
### entity
### first_name
### family_name
### first_name_original
### entity_original
### entity_original_upper
@logger.critical
def ls_entities_as_dataframe(LS_ENTITIES):
    # If there are entities
    if len(LS_ENTITIES) > 0:
        df_entities = entities_dataframe(LS_ENTITIES)
        
        df_entities = df_entities.sort_values(['id_parag'], ascending = [True])    

        # Add first_name_original columnfiter
        df_entities['first_name_original'] = df_entities['first_name']
        
        df_entities['entity_original'] = df_entities['entity']
        
        # Remove accents from 'entity'
        df_entities['entity'] = remove_accents(df_entities['entity'])
        
        # No accent and uppercase
        df_entities['entity_original_upper'] = remove_accents(df_entities['entity_original']).str.upper()
        
        df_entities_orig = df_entities
    # No entities
    else:
        df_entities = np.nan

    return df_entities    
    
      
    
  
  
# ls_postag list as a data frame  
## It returns a data.frame with variables:
### id_parag
### id_word
### word
### pos_tag
### gender
### number
@logger.critical
def ls_postag_as_dataframe(LS_POSTAG):
    # If the tokens were labeled    
    if len(LS_POSTAG) > 0:
        df_postag = pd.concat(LS_POSTAG) 
        # 'id_word' count since the beggining 
        df_postag['id_word'] = [item for item in range(0, df_postag.shape[0])]
        # re-ordering rows
        order_cols_postag = ['id_parag', 'id_word', 'word', 'pos_tag', 'gender', 'number']
        df_postag = df_postag.reindex(columns = order_cols_postag)
    else:
        df_postag = np.nan 
        
    
    return df_postag 
    
@logger.critical   
def nearest_quote_pron(DF_QUOTES_BEG_END, DF_PRONS_IDENTIFIED_POSTAG):
    list_quote_id_pair = []
    list_quote_parag = []
    list_quote_beg = []
    list_quote_end = []
    list_quote_text = []
    list_pron_parag = []
    list_word = []
    list_verb_before_quote = []
    list_verb_after_quote = []
    list_no_citation_verb = []
    list_pron = []
    list_pron_gender = []

    
    for INDEX,ROW in DF_QUOTES_BEG_END.iterrows():
        id_parag = ROW['id_parag']
        
        list_quote_id_pair.append(ROW['id_pair'])
        list_quote_parag.append(id_parag)
        list_quote_beg.append(ROW['id_quote_beg'])
        list_quote_end.append(ROW['id_quote_end'])
        list_quote_text.append(ROW['quote_text'])
        list_word.append(np.nan)
        list_verb_before_quote.append(np.nan)
        list_verb_after_quote.append(np.nan)
        list_no_citation_verb.append(np.nan)

        prons_bef_quote = DF_PRONS_IDENTIFIED_POSTAG[DF_PRONS_IDENTIFIED_POSTAG['id_parag'] <= id_parag]

        if prons_bef_quote.shape[0] == 0:
            list_pron_parag.append(np.nan)
            
            list_pron.append(np.nan)
            list_pron_gender.append(np.nan)
        else:
            prons_bef_quote_aux = prons_bef_quote.iloc[-1]
            list_pron_parag.append(int(str(prons_bef_quote_aux['id_parag'])))
            
            list_pron.append(prons_bef_quote_aux['word'])
            list_pron_gender.append(prons_bef_quote_aux['gender'])
    
    dict = {'id_pair': list_quote_id_pair,
            'id_parag': list_quote_parag,
            'id_quote_beg':list_quote_beg,
            'id_quote_end':list_quote_end,
            'quote_text': list_quote_text,
            'pron_parag': list_pron_parag,
            'word': list_word,
            'verb_before_quote': list_verb_before_quote,
            'verb_after_quote': list_verb_after_quote,
            'no_citation_verb': list_no_citation_verb,
            'pronoun': list_pron,
            'gender': list_pron_gender}
    
    df_quote_pron = pd.DataFrame(dict) 
    
    return df_quote_pron     
    
    
# It needs:
### entities_postag_format
### quotes_dataframe
### count_consecutive_entities
### concat_consecutive_entities
### identify_name_part_another_name
### all_entities_dataframe
### remove_entries_name_thathas_fullname
### replace_singlename_fullname_ifpreviouslyappeared
### add_gender_to_entities
### rebuild_df_entities_postag_when_difents_samefamname
@logger.critical
def organize_entities(DF_POSTAG,      # entities_postag_format e quotes_dataframe
                              NAMES_AUX,      # add_gender_to_entities
                              DF_QUOTES_BEG_END, # to remove entities that are inside quotes ##
                              DF_ENTITIES     # entities_postag_format
                             ): 
    # DF_POSTAG = df_postag
    # NAMES_AUX = NAMES_AUX
    # DF_QUOTES_BEG_END = df_quotes_beg_end
    # DF_ENTITIES = df_entities



    # Put entities into postag format
    df_entities_postag = entities_postag_format(DF_POSTAG = DF_POSTAG, 
                                                DF_ENTITIES = DF_ENTITIES)
        

    # If there are QUOTES:
    # Check if there are entities  to be concatenated
    df_entities_postag = df_entities_postag.sort_values(['id_ent_beg'], ascending = [True]) 
    num_consecutive_entities = count_consecutive_entities(DF_ENTITIES_POSTAG = df_entities_postag)
            
    
    # If there are entities to concatenate: do it
    if num_consecutive_entities > 0:
        while num_consecutive_entities > 0:
            # Concatenate two names that are subsequent
            df_entities_postag = concat_consecutive_entities(DF_ENTITIES_POSTAG = df_entities_postag)
            df_entities_postag = df_entities_postag.sort_values(['id_ent_beg'], ascending = [True]) 
            num_consecutive_entities = count_consecutive_entities(DF_ENTITIES_POSTAG = df_entities_postag)

    # If there are NO entities to concatenate: 'create' column to be used at 'rebuild_df_entities_postag_when_difents_samefamname'
    else:
        df_entities_postag['len_entity'] = df_entities_postag.apply(lambda row: define_len_entity(row), axis = 1)

        
    ls_entities_hug_face_concat = [(ROW['id_parag'], ROW['entity']) for INDEX,ROW in df_entities_postag.iterrows()]

    # We take as entities only the ones obtained with hugging face library
    df_entities = ls_entities_as_dataframe(ls_entities_hug_face_concat)
            
            
    # All entities identified 
    all_entities = df_entities['entity'].values.tolist()
            

    # Apply 'identify_name_part_another_name' to identify names that must be maped to full names
    df_intersec = identify_name_part_another_name(ALL_ENTITIES = all_entities)
            
    # Auxiliary object
    # to avoid future useless joins: merge to get 'id_parag' column.  
    df_entities_parag = df_entities[['id_parag', 'entity']]
    # Put all entities in a data.frame
    df_all_entities = all_entities_dataframe(DF_ENTITIES = df_entities, 
                                            DF_ENTITIES_PARAG = df_entities_parag,
                                            DF_INTERSEC = df_intersec)
            
    # Apply 'remove_entries_name_thathas_fullname' to 'df_all_entities'
    df_all_entities = remove_entries_name_thathas_fullname(DF_ALL_ENTITIES = df_all_entities)
            
    
    df_entities = replace_singlename_fullname_ifpreviouslyappeared(DF_ENTITIES = df_entities, 
                                                                            DF_ALL_ENTITIES = df_all_entities) 
    # Apply 'add_gender_to_entities' function to 'df_entities'
    df_entities_gender_aux = add_gender_to_entities(DF_ENTITIES = df_entities, 
                                                            NAMES_AUX = NAMES_AUX)
            
    df_entities_gender_aux = df_entities_gender_aux[['id_parag', 'entity_original_upper', 'entity_orig', 'entity_full_name', 'gender']].drop_duplicates()

    # Update 'df_entities_postag' with gender
    df_entities_postag = df_entities_postag.merge(df_entities_gender_aux, 
                                                    left_on = ['id_parag', 'entity_upper'],
                                                    right_on = ['id_parag', 'entity_original_upper'],
                                                    how = 'left') 

    df_entities_postag = df_entities_postag.drop(columns = ['entity_original_upper']) 
            
            
            
    ## Remove entities that are inside quotes ##

    df_quotes_beg_end_aux = DF_QUOTES_BEG_END[['id_parag', 'id_quote_beg', 'id_quote_end']]
    df_entities_postag = df_entities_postag.merge(df_quotes_beg_end_aux,
                                                    on = 'id_parag',
                                                    how = 'left')

    df_entities_postag['ent_inside_quote'] = df_entities_postag.apply(lambda row: define_entity_inside_quote(row), axis = 1)

            
    # Filter rows, select columns
    df_entities_postag = df_entities_postag[df_entities_postag['ent_inside_quote'] == 0]
    df_entities_postag = df_entities_postag.drop(columns = ['id_quote_beg', 'id_quote_end', 'ent_inside_quote'])
    df_entities_postag = df_entities_postag.drop_duplicates()
            
    # Remove expressions that are not names (that are stopwords)
    list_not_names = ['de', 'dos', 'das', 'e', 'De', 'Dos', 'Das', 'E', 'da', 'Da', 'do', 'Do']

    df_entities_postag = df_entities_postag[-df_entities_postag["entity"].isin(list_not_names)]

    # Deal with cases as 'Bolsonaro' and 'Monteiro', if any
    df_entities_postag_final = rebuild_df_entities_postag_when_difents_samefamname(df_entities_postag)
            
    del df_entities_postag

    df_entities_postag = df_entities_postag_final
            
    # Return
    list_to_return = []
            
    list_to_return.append(df_entities_gender_aux)
    list_to_return.append(df_all_entities)
    list_to_return.append(df_entities_postag)
            
    return list_to_return      
    
     


## It returns a data.frame with variables:    
### id_pair
### id_parag
### id_quote_beg
### id_quote_end
### tam_quote
### quote_language
### num_dif_grammar_class
### num_verb
### num_noun
### word_citation
### entity_verb
### id_parag_ent_verb
### ent_quote_dif_parag_verb
### ent_quote_same_parag_verb
### entity_dist
### id_parag_ent_dist
### ent_quote_dif_parag_dist
### ent_quote_same_parag_dist
### entity_note
### id_parag_ent_note
### ent_quote_dif_parag_note
### ent_quote_same_parag_note
### quote_text_x
### entity_full_name
### id_parag_ent
### id_ent_beg
### id_ent_end
### quote_text_y
@logger.critical
def put_everything_together(df_ent_quote_verbs,
                           df_ent_quote_dist,
                           df_note_quote_dist,
                           df_pron,
                           df_quotes_beg_end):
    
    df_info_quote = df_quote_verbs_aux = df_quotes_beg_end[['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 
                                                    'tam_quote', 
                                                     #'quote_text', 
                                                     'quote_language', 
                                                    'num_dif_grammar_class', 'num_verb', 'num_noun']]
    
    verbs = df_info_quote.merge(df_ent_quote_verbs,
                          on = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end'],
                          how = 'outer')
    
    # VERBS + DIST

    # df_ent_quote_verbs
    verbs_dist = verbs.merge(df_ent_quote_dist,
                              on = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end'],
                              how = 'outer')
    
    # VERBS + DIST + NOTES
    verbs_dist_note = verbs_dist.merge(df_note_quote_dist,
                                       on = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end'], 
                                       how = 'outer')
    
    # VERBS + DIST + NOTES + PRONOUNS 
    verbs_dist_note_pron = verbs_dist_note.merge(df_pron,
                                                   on = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end'], 
                                                   how = 'outer')
    
    # Recover quote text itself
    df_quotes_beg_end_aux = df_quotes_beg_end[['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end', 'quote_text']]

    verbs_dist_note_pron = verbs_dist_note_pron.merge(df_quotes_beg_end_aux,
                                                      on = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end'],
                                                      how = 'left')
    
    return verbs_dist_note_pron
    
    
    
    
    
    
    
# It gets all quotes drom DF_POSTAG dataframe and it takes metrics/statistics
# It needs:
### define_odds_even
# It returns:
## 999999 it there was a mistake OR
## a dataframe with variables:
### id_pair:               quotes pair number
### id_parag:              paragraph number
### id_quote_begin:        position of the quotation mark that opens the quote pair
### id_quote_end:          position of the quotation mark that closes the quote pair
### tam_quote:             number of words in the quote
### quote_text:            quote text itself
### quote_language:        quote language
### num_dif_grammar_class: number of distinct grammar classes
### num_verb:              number of verbs
### num_noun:              number of nouns
@logger.critical
def quotes_dataframe(DF_POSTAG):

    # words in Capital letter to merge
    DF_POSTAG['word_upper'] = DF_POSTAG['word'].str.upper()
    
    # Entries that are '"'
    only_quotes = DF_POSTAG[DF_POSTAG['word_upper'] == '"']
    only_quotes = only_quotes.drop(columns = ['word', 'pos_tag', 'gender', 'number', 'word_upper'])
    
    num_rows = only_quotes.shape[0]
    
    
    if (num_rows % 2) != 0: # NOT ALL quotes are paired: We try to stay with pair of quotes
    	# How many quotes by paragraph
        only_quotes['num_quotes_by_parag'] = only_quotes.groupby(['id_parag'])['id_parag'].transform('count')
        
        # 'odds_pair_quotes' is 0 if quotes are paired and 1 if they are not paired
        only_quotes['odds_pair_quotes'] = only_quotes.apply(lambda row: define_odds_even(row), axis = 1)
        
        # Filter to keep only paired quotes
        only_quotes = only_quotes.query('odds_pair_quotes == 0')
        
        # Drop columns
        only_quotes = only_quotes.drop(columns = ['num_quotes_by_parag', 'odds_pair_quotes'])

    # Reorder rows, just in case
    only_quotes = only_quotes.sort_values(['id_parag', 'id_word'], ascending = [True, True]) 
    
    # New index column
    only_quotes = only_quotes.reset_index() 
    only_quotes['new_index'] = [item for item in range(0, only_quotes.shape[0])]

    num_rows = only_quotes.shape[0]
    
    
    if (num_rows % 2) == 0: # All quotes are paired
        # Split quotes data.frame in 2: 'beggining' and 'end'
        even_rows = list(range(0, num_rows, 2))
        odd_rows = list(range(1, num_rows, 2))

        # Filter entries that correspond to the quotes beggining
        quotes_begin = only_quotes.filter(items = even_rows, axis = 0)
        quotes_begin = quotes_begin.drop(columns = ['new_index'])
        quotes_begin['id_pair'] = [item for item in range(0, quotes_begin.shape[0])]

        quotes_begin = quotes_begin.set_index('index')
        quotes_begin = quotes_begin.rename(columns = {'id_word':'id_quote_beg'})

        # Filter entries that correspond to the quotes end
        quotes_end = only_quotes.filter(items = odd_rows, axis = 0)
        quotes_end = quotes_end.drop(columns = ['new_index'])
        quotes_end['id_pair'] = [item for item in range(0, quotes_end.shape[0])]

        quotes_end = quotes_end.set_index('index')
        quotes_end = quotes_end.rename(columns = {'id_word':'id_quote_end'})

        # Join 'quotes_begin' and 'quotes_end'
        quotes_beg_end = quotes_begin.merge(quotes_end, 
                                on = ['id_parag', 'id_pair'],
                                how = 'outer')
        quotes_beg_end = quotes_beg_end.reindex(columns = ['id_pair', 'id_parag', 'id_quote_beg', 'id_quote_end'])

        # Add new column with quote size/length
        quotes_beg_end['tam_quote'] = quotes_beg_end['id_quote_end'] - quotes_beg_end['id_quote_beg'] - 1 
        
        
        # Add new column with quote itself
        ls_quote_text = []
        #  Add new column with quote language
        ls_quote_language = []
        # Add new column with number of distinct grammar class
        ls_num_dif_grammar_class = []
        # Add new column with number of verbs
        ls_num_verb = []
        # Add new column with number of nouns
        ls_num_noun = []

        
        for INDEX,ROW in quotes_beg_end.iterrows():
            beg = ROW['id_quote_beg']
            end = ROW['id_quote_end']
            
            subset_df_postag = DF_POSTAG.iloc[(beg + 1):end]
            
            # text itself
            quote_text = " ".join(subset_df_postag['word'])        
            ls_quote_text.append(quote_text)
            
            # language
            quote_language = detect(quote_text)
            ls_quote_language.append(quote_language)
            
            # number of distinct grammar class
            num_dif_grammar_class = subset_df_postag['pos_tag'].nunique()
            # is there any verb?
            subset_verb = subset_df_postag[subset_df_postag['pos_tag'] == "VERB"]
            num_verb = subset_verb.shape[0]
            # is there any noun?
            subset_noun = subset_df_postag[subset_df_postag['pos_tag'] == "NOUN"]
            num_noun = subset_noun.shape[0]
            
            ls_num_dif_grammar_class.append(num_dif_grammar_class)
            ls_num_verb.append(num_verb)
            ls_num_noun.append(num_noun)
        
        # Add these new variables to object
        quotes_beg_end['quote_text'] = ls_quote_text
        quotes_beg_end['quote_language'] = ls_quote_language
        quotes_beg_end['num_dif_grammar_class'] = ls_num_dif_grammar_class
        quotes_beg_end['num_verb'] = ls_num_verb
        quotes_beg_end['num_noun'] = ls_num_noun

        return quotes_beg_end
    
    else:
        return 999999     
    

# To read txt file and to replace quotes by a single pattern
# To return a character/string with the original text cleaned/processed.
@logger.critical
def read_txtfile(PATH_NEWSTEXT, ARTICLEID):
    # To read the data
    file_to_read = open(PATH_NEWSTEXT + ARTICLEID, "r+")
    text = file_to_read.read()
    
    # To replace “ and ” by "
    text = text.replace('“', '"')
    text = text.replace('”', '"')
    
    return text


# To read txt file and to replace quotes by a single pattern
# To return a character/string with the original text cleaned/processed.
@logger.critical
def read_txtfile(PATH_NEWSTEXT):
    # To read the data
    file_to_read = open(PATH_NEWSTEXT, "r+", encoding="utf8")
    text = file_to_read.read()
    
    # To replace “ and ” by "
    text = text.replace('“', '"')
    text = text.replace('”', '"')
    
    return text
    

# To deal with cases as 'Bolsonaro' and 'Monteiro', if any
# It return a data.frame with:
### id_parag	
### entity	
### entity_upper	
### id_ent_beg	
### id_ent_end	
### len_entity		
### entity_orig	
### entity_full_name	
### gender
@logger.critical
def rebuild_df_entities_postag_when_difents_samefamname(DF_ENTITIES_POSTAG):

    # Variable to count how many names was maped to a family name
    num_id_ent_beg = DF_ENTITIES_POSTAG.groupby(by = 'id_ent_beg')['id_ent_beg'].count()
    dict_num_id_ent_beg = {'num_id_ent_beg': num_id_ent_beg}
    df_num_id_ent_beg = pd.DataFrame(data = dict_num_id_ent_beg)


    DF_ENTITIES_POSTAG = DF_ENTITIES_POSTAG.merge(df_num_id_ent_beg, 
                                 on = 'id_ent_beg',
                                 how = 'left')

    # Split data.frame in equal and dif and dif into 1 and gt1
    df_entities_postag_aux_equal = DF_ENTITIES_POSTAG[DF_ENTITIES_POSTAG['len_entity'] == DF_ENTITIES_POSTAG['num_id_ent_beg']]
    df_entities_postag_aux_dif = DF_ENTITIES_POSTAG[DF_ENTITIES_POSTAG['len_entity'] != DF_ENTITIES_POSTAG['num_id_ent_beg']]
    df_entities_postag_aux_gt1 = df_entities_postag_aux_dif[df_entities_postag_aux_dif['len_entity'] > 1].drop_duplicates()
    # df_entities_postag_aux_1 deals with 'Bolsonaro' and 'Monteiro'
    df_entities_postag_aux_1 = df_entities_postag_aux_dif[df_entities_postag_aux_dif['len_entity'] == 1].drop_duplicates()
    
    if df_entities_postag_aux_1.shape[0] >= 1:

         # For each family name associate it to the first complete name it was paired with
        all_ent_famname = df_entities_postag_aux_1['entity_upper'].drop_duplicates()
        ls_all_ent_famname = []

        for ent in all_ent_famname:
            subdf = df_entities_postag_aux_1[df_entities_postag_aux_1['entity_upper'] == ent]
            subdf_cols = list(subdf.columns.values)
            
            if 'id_parag' in subdf_cols:
                subdf = subdf.drop(columns = ['id_parag'])
            if 'entity' in subdf_cols:
            	subdf = subdf.drop(columns = ['entity'])   
            if 'id_ent_beg' in subdf_cols:
            	subdf = subdf.drop(columns = ['id_ent_beg'])
            if 'id_ent_end' in subdf_cols:
            	subdf = subdf.drop(columns = ['id_ent_end']) 
            if 'len_entity' in subdf_cols:
            	subdf = subdf.drop(columns = ['len_entity'])
            if 'single_name_original' in subdf_cols:
            	subdf = subdf.drop(columns = ['single_name_original'])             	

            subdf = subdf.iloc[0]
            ls_all_ent_famname.append(subdf)


        # From list to dataframe 
        if len(ls_all_ent_famname) == 1:
            df_all_ent_famname = ls_all_ent_famname[0].to_frame().transpose()
        elif len(ls_all_ent_famname) > 1:
            df_all_ent_famname = ls_all_ent_famname[0].to_frame().transpose()
            for i in range(1, len(ls_all_ent_famname)):
                df_all_ent_famname_aux = ls_all_ent_famname[i].to_frame().transpose()
                df_all_ent_famname = pd.concat([df_all_ent_famname, df_all_ent_famname_aux], 
                           				ignore_index = True,
                           				sort = False)
        else:
            print('ERRO')



        # Join the new 'map' to 'df_entities_postag_aux_1'
        df_entities_postag_aux_1 = df_entities_postag_aux_1.drop(columns = ['entity_orig', 'entity_full_name', 'gender', 'num_id_ent_beg'])

        df_entities_postag_aux_1 = df_entities_postag_aux_1.merge(df_all_ent_famname,
                                                                 on = 'entity_upper',
                                                                 how = 'left')

        df_entities_postag_aux_1 = df_entities_postag_aux_1.drop_duplicates()

        ## all conditions together
        df_entities_postag_rebuild = pd.concat([df_entities_postag_aux_equal, 
                                df_entities_postag_aux_gt1, 
                                df_entities_postag_aux_1], ignore_index = True)
        # Final adjustements
        df_entities_postag_rebuild = df_entities_postag_rebuild.sort_values(['id_parag', 'id_ent_beg'], ascending = [True, True])

        df_entities_postag_rebuild = df_entities_postag_rebuild.drop_duplicates().reset_index() 

        df_entities_postag_rebuild = df_entities_postag_rebuild.drop(columns = ['index', 'num_id_ent_beg'])

        return df_entities_postag_rebuild

    else:
        return DF_ENTITIES_POSTAG    
    
    
    
    
@logger.critical
def recognize_note_terms_put_as_df_entities(NOTE_LIST, DF_POSTAG):
    termos_nota_df = pd.DataFrame(NOTE_LIST, columns = ['word_upper'])
    termos_nota_df = termos_nota_df.assign(pos_tag = 'NOUN')
    termos_nota_df = termos_nota_df.assign(note_citation = 1)
    
    # Para trazer parágrafo
    termos_nota_postag_df = DF_POSTAG.merge(termos_nota_df, 
                            on = ['word_upper', 'pos_tag'],
                            how = 'left')
    termos_nota_postag_df = termos_nota_postag_df[termos_nota_postag_df['note_citation'] == 1]
    
    
    # Remove columns
    termos_nota_postag_df.drop('gender', axis = 1, inplace = True)
    termos_nota_postag_df.drop('number', axis = 1, inplace = True)
    termos_nota_postag_df.drop('note_citation', axis = 1, inplace = True)
    termos_nota_postag_df.drop('id_word', axis = 1, inplace = True)
    termos_nota_postag_df.drop('pos_tag', axis = 1, inplace = True)
    
    # Create 'entity_original'
    termos_nota_postag_df = termos_nota_postag_df.assign(entity_original = termos_nota_postag_df['word'])

    # Rename columns
    termos_nota_postag_df = termos_nota_postag_df.rename(columns = {'word':'entity', 
                                                                    'word_upper':'entity_original_upper'})
    
    # Create columns
    termos_nota_postag_df = termos_nota_postag_df.assign(first_name = termos_nota_postag_df['entity'].str.upper())
    termos_nota_postag_df = termos_nota_postag_df.assign(first_name_original = termos_nota_postag_df['first_name'])
    termos_nota_postag_df = termos_nota_postag_df.assign(family_name = np.nan)

    # Re-ordering columns
    order_cols = ['id_parag', 'entity', 'first_name', 'family_name', 'first_name_original', 'entity_original', 'entity_original_upper']
    termos_nota_postag_df = termos_nota_postag_df.reindex(columns = order_cols)

    return termos_nota_postag_df
    
    
    
    
# 'termos_pron_postag_df' como 'df_all_entities'
# It needs:
### define_pron_inside_quotes
# It returns a data.frame with columns:
### complete_name
### len_complete_name
### single_name
### single_name_upper
### single_name_original
### id_parag_all
### entity
@logger.critical
def recognize_pronouns_put_as_df_all_entities(PRONOUNS_LIST, 
                                              DF_POSTAG,
                                              DF_QUOTES_BEG_END):
    #PRONOUNS_LIST = ['ELE', 'ELA']
    #DF_POSTAG = df_postag
    #DF_QUOTES_BEG_END = df_quotes_beg_end_aux
    
    termos_pron_df = pd.DataFrame(PRONOUNS_LIST, columns = ['word_upper'])
    termos_pron_df = termos_pron_df.assign(pos_tag = 'PRON')
    termos_pron_df = termos_pron_df.assign(gender = ['M', 'F'])
    termos_pron_df = termos_pron_df.assign(pronoun = 1)
    
    # Para trazer parágrafo
    termos_pron_postag_df = DF_POSTAG.merge(termos_pron_df, 
                                        on = ['word_upper', 'pos_tag'],
                                        how = 'left')
    termos_pron_postag_df = termos_pron_postag_df[termos_pron_postag_df['pronoun'] == 1]
    
    
    num_parag_recognized = termos_pron_postag_df.shape[0]
    
    # If there are NO pronouns recognized
    if num_parag_recognized == 0:
        return 999999
    # If there are pronouns recognized
    else:
        # Remove columns
        termos_pron_postag_df.drop('gender_y', axis = 1, inplace = True)
        termos_pron_postag_df.drop('number', axis = 1, inplace = True)
        termos_pron_postag_df.drop('pronoun', axis = 1, inplace = True)
        termos_pron_postag_df.drop('pos_tag', axis = 1, inplace = True)
        termos_pron_postag_df = termos_pron_postag_df.rename(columns = {'gender_x':'gender'})
        
        # To remove pronouns that occur inside quotes we join with 'DF_QUOTES_BEG_END'
        termos_pron_postag_df = termos_pron_postag_df.merge(DF_QUOTES_BEG_END,
                                                            on = 'id_parag',
                                                            how = 'left')

        # Apply 'define_pron_inside_quote' by row    
        termos_pron_postag_df['pron_inside_quote'] = termos_pron_postag_df.apply(lambda row: define_pron_inside_quote(row), axis = 1)

        termos_pron_inside_quote = termos_pron_postag_df[termos_pron_postag_df['pron_inside_quote'] == 1] 

        # Filter quote pairs that do not have a pronoun inside    
        termos_pron_inside_quote_id_word = termos_pron_inside_quote['id_word']  
        termos_pron_postag_df = termos_pron_postag_df[~termos_pron_postag_df.id_word.isin(termos_pron_inside_quote_id_word)]

        termos_pron_postag_df = termos_pron_postag_df.drop(columns = ['id_quote_beg', 'id_quote_end', 'pron_inside_quote', 'quote_text'])
        termos_pron_postag_df = termos_pron_postag_df.drop_duplicates()


        pron_as_df_all_entities = termos_pron_postag_df

        # Create columns
        pron_as_df_all_entities = pron_as_df_all_entities.assign(complete_name = pron_as_df_all_entities['word'])
        pron_as_df_all_entities = pron_as_df_all_entities.assign(len_complete_name = 1)
        pron_as_df_all_entities = pron_as_df_all_entities.assign(single_name = pron_as_df_all_entities['word'])
        pron_as_df_all_entities = pron_as_df_all_entities.assign(single_name_upper = pron_as_df_all_entities['word_upper'])
        pron_as_df_all_entities = pron_as_df_all_entities.assign(single_name_original = pron_as_df_all_entities['word'])
        pron_as_df_all_entities = pron_as_df_all_entities.assign(entity = pron_as_df_all_entities['word'])

        # Rename columns
        pron_as_df_all_entities = pron_as_df_all_entities.rename(columns = {'id_parag':'id_parag_all'})
        # Remove columns
        pron_as_df_all_entities.drop('word', axis = 1, inplace = True)
        pron_as_df_all_entities.drop('word_upper', axis = 1, inplace = True)

        # Select and reorder columns
        # Reorder columns/variables
        order_cols = ['complete_name', 'len_complete_name', 
                      'single_name', 'single_name_upper', 
                      'single_name_original', 'id_parag_all', 
                      'entity', 'gender']

        pron_as_df_all_entities = pron_as_df_all_entities.reindex(columns = order_cols)


        return [termos_pron_postag_df, pron_as_df_all_entities]     
    
     
    
    
    
    
    
# A data.frame with the verbs positions
# It returns a data.frame with:
## 'id_parag'
## 'word_upper'
## 'pos_tag'
## 'word_citation'
@logger.critical
def recognize_verbs_in_paragraphs(DF_QUOTES_BEG_END, LIST_VERBS, PARAGRAPHS):
    #DF_QUOTES_BEG_END = df_quotes_beg_end   
    #LIST_VERBS = VERBS
    #PARAGRAPHS = paragraphs
    
    all_parag_with_quotes = DF_QUOTES_BEG_END['id_parag'].drop_duplicates()
    list_verbs_found = []
    list_parag = []
    
    
    
    for parag in all_parag_with_quotes:
        texto_exemplo = PARAGRAPHS[parag]
        # LISTA SOMENTE DE APOIO
        aspas = []
        # LISTA A SER USADA
        aspas_em_duplas = []

        # PARA OBTER OS INDICES DAS ASPAS
        for index, c in enumerate(texto_exemplo):
            if c == "\"":
                aspas.append(index)

        # ORGANIZANDO AS ASPAS EM TUPLAS (INICIO, FIM+1)
        for index, aspa in enumerate(aspas):
            # INDICE IMPAR
            if index % 2 == 1:
                dupla_de_apas = (aspas[index-1], aspas[index] + 1)
                aspas_em_duplas.append(dupla_de_apas)

        # TEXTO SEM AS ASPAS
        result = ''.join(chr for idx, chr in enumerate(texto_exemplo, 1) if not any(strt_idx <= idx <= end_idx for strt_idx, end_idx in aspas_em_duplas))
        
        
        for verb in LIST_VERBS:
            result_upper = result.upper()
            if re.search(verb, result_upper):
                list_parag.append(parag)
                list_verbs_found.append(verb)
                
                

    dict = {'id_parag': list_parag,
            'word_upper': list_verbs_found,
            'pos_tag': 'VERB',
            'word_citation': 1}
  
    df = pd.DataFrame(data = dict)
    
    return df    
    
    


# To return the expression in double quotes, if it has more than a word
# Library: re
# It is used at 'text_in_doublequotes'
@logger.critical
def regex_inside_doublequotes(STRING):
    expres = re.findall(r'“.*?”|".*?"', STRING)
    if(len(expres) > 0):
        space = re.findall(r'[\s]+', expres[0])
        if(len(space) > 0):
            return expres[0]
    else:
        return ''
    return '' 
    
    
    
@logger.critical    
def remove_accents(STRING):
    # Remove accents from first name to merge/join with 'DF_ENTITIES_GENDER'
    STRING = STRING.str.normalize('NFKD').str.encode('ascii', errors = 'ignore').str.decode('utf-8')

    # 2nd try
    dic_accents = {'à':'a', 'á':'a', 'â':'a', 'ã':'a', 'ä':'a', 'è':'e', 'é':'e', 'ê':'e', 'ë':'e', 'ì':'i', 'í':'i', 'î':'i', 'ï':'i', 'ò':'o', 'ó':'o', 'ô':'o', 'õ':'o', 'ö':'o', 'ù':'u', 'ú':'u', 'û':'u', 'ü':'u', 'À':'A', 'Á':'A', 'Â':'A', 'Ã':'A', 'Ä':'A', 'È':'E', 'É':'E', 'Ê':'E', 'Ë':'E', 'Ì':'I', 'Í':'I', 'Î':'I', 'Ò':'O', 'Ó':'O', 'Ô':'O', 'Õ':'O', 'Ö':'O', 'Ù':'U', 'Ú':'U', 'Û':'U', 'Ü':'U', 'ç':'c', 'Ç':'C', 'ñ':'n', 'Ñ':'N'}

    for letter_accent, letter_no_accent in dic_accents.items():
    	STRING = STRING.replace(letter_accent, letter_no_accent)
        
    return STRING      
    
    
    
    
# This function removes entities as 'Covid', 'Não' and 'Deus' from LS_ENTITIES
@logger.critical
def remove_entities_not_consider_from_ls_entities(LS_ENTITIES, LS_ENTITIES_NOT_CONSIDER):
    ls_entities_clean = []
    for pair in LS_ENTITIES:
        ent = pair[1]
        if ent in LS_ENTITIES_NOT_CONSIDER:
            continue
        else:
            ls_entities_clean.append(pair)
            
    return ls_entities_clean   
   



# Input: - NOT BEING USED
## List (character/string)
# Output 0: a dataframe with:
## parag_id_quote: paragraph index where the quotes was found
## original_parag: paragraph where the quotes was found
## inside_quotes: text that was found inside quotes
# Output 1: a list with:
## paragraph index where there is a quote
# It uses:
## regex_inside_doublequotes
## condition_x_notempty
# Library: pandas as pd
@logger.critical
def text_in_doublequotes(text_paragraphs):
    text_quotes = []
    text_quotes_index = []
    df_quote = pd.DataFrame()
    
    for paragraph_index, paragraph in enumerate(text_paragraphs):
        # checking for double quotes in the paragraph
        paragraph_quotes = re.findall(r'“.*?”|".*?"', paragraph)
        if(len(paragraph_quotes) > 0):
            for quote in paragraph_quotes:
                # checking for spaces between words
                # only accepting quotes with more than two words
                space_between_words = re.findall(r'[\s]+', quote)
                if(len(space_between_words) > 0):
                    text_quotes.append([paragraph_index, paragraph, quote])
                    text_quotes_index.append(paragraph_index)
    
    df_quote = pd.DataFrame(text_quotes, columns = ['parag_id_quote', 'original_parag', 'inside_quotes'])

    return [df_quote, text_quotes_index]






    
    


    
    





# It returns objetcs that are used to get the entities context - NOT BEING USED
# Two dataframes as arguments
## DF_ENTITIES_GENDER:
### id_parag	entity	first_name	family_name	gender
## DF_POSTAG:
### id_parag	id_word	word	pos_tag	gender	number	word_upper
# To return 02 dataframes in a list with the same columns:
## (0) df_only_ent:
## (1) df_noun_adj_ent:
### id_parag
### id_word
### word
### pos_tag
### gender
### number
# It returns objetcs that are used to get the entities context
# Input
## DF_ENTITIES_GENDER dataframe:
### id_parag	entity	first_name	family_name	gender
## DF_POSTAG dataframe:
### id_parag	id_word	word	pos_tag	gender	number	word_upper
# Output: 02 dataframes in a list with the same columns:
## (0) df_only_ent:
## (1) df_noun_adj_ent:
### id_parag
### id_word
### word
### pos_tag
### gender
### number
### word_upper
@logger.critical
def objects_to_context(DF_ENTITIES_GENDER, DF_POSTAG):
     # Binary column to identify that the entry is an entity
    DF_ENTITIES_GENDER = DF_ENTITIES_GENDER.assign(ent = 1)
    
    
    DF_POSTAG['word_upper'] = remove_accents(DF_POSTAG['word_upper'])    

    
    # 'df_entities' in the same format as 'df_postag' to concat (rbind) 'df_noun' and 'df_adj'
    df_ent_as_postag = DF_ENTITIES_GENDER.merge(DF_POSTAG, 
                                                left_on = ['id_parag', 'first_name_original'],
                                                right_on = ['id_parag', 'word_upper'],
                                                how = 'left')
    
    df_ent_as_postag = df_ent_as_postag[['id_parag', 'id_word', 'entity', 'pos_tag', 'gender_x', 'number', 'ent']]
    df_ent_as_postag = df_ent_as_postag.rename(columns = {'entity': 'word', 'gender_x': 'gender'})
    df_ent_as_postag = df_ent_as_postag.drop_duplicates()
    df_ent_as_postag = df_ent_as_postag.sort_values(['id_parag', 'id_word'], ascending = [True, True])        
    
    # Text dataframe with nouns and adjectives, only
    df_noun = DF_POSTAG[DF_POSTAG['pos_tag'] == "NOUN"]
    df_adj = DF_POSTAG[DF_POSTAG['pos_tag'] == "ADJ"]
    df_noun = df_noun.assign(ent = 0)
    df_adj = df_adj.assign(ent = 0)
    
    # Text dataframe with nouns, adjectives and entities
    df_noun_adj_ent = pd.concat([df_noun, df_adj, df_ent_as_postag], axis = 0)
    # Rearrange rows
    df_noun_adj_ent = df_noun_adj_ent.sort_values(by = ['id_parag', 'id_word'], ascending = True)
    # New column based on this re-arrangement
    df_noun_adj_ent['new_index'] = [item for item in range(0, df_noun_adj_ent.shape[0])]
    # Setting 'new_index' column as index
    df_noun_adj_ent = df_noun_adj_ent.set_index('new_index')
    
    # Only entities
    df_only_ent = df_noun_adj_ent[df_noun_adj_ent['ent'] == 1]
    df_only_ent = df_only_ent.sort_index()
    # Remove 'ent' & 'word_upper' column/variable
    df_only_ent = df_only_ent.drop(columns = ['ent', 'word_upper'])
    
    
    # Remove 'ent' & 'word_upper' column/variable
    df_noun_adj_ent = df_noun_adj_ent.drop(columns = ['ent', 'word_upper'])
    
    # Gender in a single pattern
    dic_gender = {'Fem':'F', 'Masc':'M'}

    for word, letter in dic_gender.items():
        df_noun_adj_ent['gender'] = df_noun_adj_ent['gender'].replace(word, letter)
    
    
    return [df_only_ent, df_noun_adj_ent]
    
    
    
# To replace a single name by a full name only if it has previously appeared
# It returns a data.frame with:
### id_parag
### first_name
### family_name
### first_name_original
### entity_original
### entity_original_upper
### single_name_original
### entity
@logger.critical
def replace_singlename_fullname_ifpreviouslyappeared(DF_ENTITIES, DF_ALL_ENTITIES):

    # Remove 'entity' column
    DF_ENTITIES = DF_ENTITIES.drop('entity', axis = 1)


    # Reorder rows
    DF_ALL_ENTITIES = DF_ALL_ENTITIES.sort_values('id_parag_all', ascending = True)


    ###
    # Try to maximize the number of entities with 'full/complete' name
    df_entities1 = DF_ENTITIES.merge(DF_ALL_ENTITIES, 
                                    left_on = 'first_name',         # df_entities
                                    right_on = 'single_name_upper', # df_all_entities
                                    how = 'left')


    # To replace a single name by a full name only if it has previously appeared
    df_entities1 = df_entities1.query('id_parag_all <= id_parag')

    df_entities1 = df_entities1.drop(columns = ['complete_name', 'single_name', 
                                              'single_name_upper', 'len_complete_name', 
                                              'id_parag_all'
                                              ])

    # Unique entries
    df_entities1 = df_entities1.drop_duplicates()
    
    ###
    # Try to maximize the number of entities with 'full/complete' name
    df_entities2 = DF_ENTITIES.merge(DF_ALL_ENTITIES, 
                                    left_on = 'entity_original',#'first_name',         # DF_ENTITIES # 
                                    right_on = 'entity_orig', #'single_name_upper', # DF_ALL_ENTITIES # 
                                    how = 'left')

    # To replace a single name by a full name only if it has previously appeared
    df_entities2 = df_entities2.query('id_parag_all <= id_parag')

    df_entities2 = df_entities2.drop(columns = ['complete_name', 'single_name', 
                                              'single_name_upper', 'len_complete_name', 
                                              'id_parag_all'
                                              ])

    # Unique entries
    df_entities2 = df_entities2.drop_duplicates()
    
    ###
    
    df_entities = pd.concat([df_entities1, df_entities2], axis = 0)
    df_entities = df_entities.drop_duplicates()
    df_entities = df_entities.sort_values('id_parag', ascending = True)

    
    return df_entities    
    
@logger.critical   
def replace_singlename_fullname_ifpreviouslyappeared2(DF_ENTITIES, DF_ALL_ENTITIES):    
    # Remove 'entity' column
    DF_ENTITIES = DF_ENTITIES.drop('entity', axis = 1)


    # Reorder rows
    DF_ALL_ENTITIES = DF_ALL_ENTITIES.sort_values('id_parag_all', ascending = True)



    # Try to maximize the number of entities with 'full/complete' name
    DF_ENTITIES = DF_ENTITIES.merge(DF_ALL_ENTITIES, 
                                    left_on = 'entity_original',#'first_name',         # DF_ENTITIES # 
                                    right_on = 'entity_orig', #'single_name_upper', # DF_ALL_ENTITIES # 
                                    how = 'left')

    # To replace a single name by a full name only if it has previously appeared
    DF_ENTITIES = DF_ENTITIES.query('id_parag_all <= id_parag')

    DF_ENTITIES = DF_ENTITIES.drop(columns = ['complete_name', 'single_name', 
                                              'single_name_upper', 'len_complete_name', 
                                              'id_parag_all'
                                              ])

    # Unique entries
    DF_ENTITIES = DF_ENTITIES.drop_duplicates()
    
    return DF_ENTITIES
    
    

# Remove entries that are from a name that has full name (ex.: Larissa is removed if there is Larissa Sayuri)
# It returns a data.frame with:
### complete_name
### len_complete_name
### single_name
### single_name_upper
### single_name_original
### id_parag_all
### entity
@logger.critical
def remove_entries_name_thathas_fullname(DF_ALL_ENTITIES):
    
    only_one_name = DF_ALL_ENTITIES[DF_ALL_ENTITIES['len_complete_name'] == 1]

    for INDEX,ROW in only_one_name.iterrows():
        single_name = ROW['single_name']

        aux = DF_ALL_ENTITIES[DF_ALL_ENTITIES['single_name'] == single_name]
        ent_01_name = aux[aux['len_complete_name'] == 1]
        ent_more_01_name = aux[aux['len_complete_name'] > 1]

        if ent_more_01_name.shape[0] >= 1:
            index_to_remove = ent_01_name.index
            DF_ALL_ENTITIES = DF_ALL_ENTITIES.drop(index_to_remove)

    return DF_ALL_ENTITIES    
    



# To save a txt file as LOG message
@logger.critical
def save_log(PATH_LOG, TYPE_LOG, ARTICLEID):  
    if not os.path.exists(PATH_LOG):
        Path(PATH_LOG).mkdir(parents = True, exist_ok = True)

    # Path 
    path_save_log = PATH_LOG + '/' + TYPE_LOG 

    if not os.path.exists(path_save_log):
        Path(path_save_log).mkdir(parents = True, exist_ok = True)
  
    with open(path_save_log + '/' + ARTICLEID, 'w') as writefile:
        ARTICLEID_notxt = ARTICLEID[0:len(ARTICLEID) - 4]
        log_message = ARTICLEID_notxt + '/' + str(datetime.datetime.today())
        writefile.write(log_message)





# It depends on:
####     create_df
@logger.critical
def save_file(ARTICLEID, DF, PATH_SAVE, HEADER):
    df_param_aux = create_df(ARTICLEID, DF.shape[0])
    
    df_final = pd.concat([df_param_aux.reset_index(drop = True), 
                        DF.reset_index(drop = True)], 
                        axis = 1)
    
    # Write INFO to file
    name_save = str(ARTICLEID) +  '.csv' 

    if not os.path.exists(PATH_SAVE):
        Path(PATH_SAVE).mkdir(parents = True, exist_ok = True)

    df_final_numpy = df_final.to_numpy()
    np.savetxt(PATH_SAVE + name_save, 
             df_final_numpy, 
             header = HEADER,
             comments = '',
             fmt = '%s', 
             delimiter = '\t')    
    
    



# It returns a data.frame with:
### id_pair
### id_parag
### id_quote_beg
### id_quote_end
### tam_quote
### quote_language
### num_dif_grammar_class
### num_verb
### num_noun
### word_citation
### entity_verb
### id_parag_ent_verb
### ent_quote_dif_parag_verb,
### ent_quote_same_parag_verb,
### entity_dist,
### id_parag_ent_dist,
### ent_quote_dif_parag_dist
### ent_quote_same_parag_dist
### entity_note
### id_parag_ent_note
### ent_quote_dif_parag_note
### ent_quote_same_parag_note
### entity_pron
### id_parag_ent_pron
### ent_quote_dif_parag_pron
### ent_quote_same_parag_pron
### quote_text
### entity_final
### crit_entity_final
@logger.critical
def verbs_dist_note_pron_define_final_entity(VERBS_DIST_NOTE_PRON, K):
    #VERBS_DIST_NOTE_PRON = verbs_dist_note_pron
    #K = 3
    
    ## -- 01 -- ##
    # If there are entities after verbs
    stronger_crit = VERBS_DIST_NOTE_PRON[VERBS_DIST_NOTE_PRON['entity_verb'].notnull()]
    remain = VERBS_DIST_NOTE_PRON[VERBS_DIST_NOTE_PRON['entity_verb'].isnull()]
    # entity_final
    stronger_crit = stronger_crit.assign(entity_final = stronger_crit['entity_verb'],
                                         crit_entity_final = 1)
    
    
    ## -- 02 -- ##
    # If there are entities in the same paragraphs from quotes
    sec_stronger_crit = remain[remain['ent_quote_same_parag_dist'] == 1]  
    remain = remain[remain['ent_quote_same_parag_dist'] != 1]
    # entity_final
    sec_stronger_crit = sec_stronger_crit.assign(entity_final = sec_stronger_crit['entity_dist'],
                                         crit_entity_final = 2)
    
    
    ## -- 03 -- ##
    # If there are NOTE expressions in the same paragraph from quote
    third_stronger_crit = remain[remain['ent_quote_same_parag_note'] == 1]
    remain = remain[remain['ent_quote_same_parag_note'] != 1]
    # entity_final
    third_stronger_crit = third_stronger_crit.assign(entity_final = third_stronger_crit['entity_note'],
                                         crit_entity_final = 3)
    
    
    ## -- 04 -- ##
    # If there are PRONOUN expressions in the same paragraph from quote
    forth_stronger_crit = remain[remain['entity_pron'].notnull()]
    remain = remain[remain['entity_pron'].isnull()]
    # entity_final
    forth_stronger_crit = forth_stronger_crit.assign(entity_final = forth_stronger_crit['entity_pron'],
                                         crit_entity_final = 4)
    
    

    ## -- 05 -- ##
    # If there are NOTE expressions in AT MOST K paragraphs BEFORE quote
    fifth_stronger_crit = remain[remain['ent_quote_dif_parag_note'] <= K]
    remain = remain[(remain['ent_quote_dif_parag_note'] > K) | np.isnan(remain['ent_quote_dif_parag_note'])]
    # entity_final
    fifth_stronger_crit = fifth_stronger_crit.assign(entity_final = fifth_stronger_crit['entity_note'],
                                                     crit_entity_final = 5)

    
    
    ## -- 06 -- ##
    # If there are PRONOUN expressions in AT MOST K paragraphs BEFORE quote
    sixth_stronger_crit = remain[remain['ent_quote_dif_parag_pron'] <= K]
    remain = remain[(remain['ent_quote_dif_parag_pron'] > K) | np.isnan(remain['ent_quote_dif_parag_pron'])]
    # entity_final
    sixth_stronger_crit = sixth_stronger_crit.assign(entity_final = sixth_stronger_crit['entity_pron'],
                                         crit_entity_final = 6)
    
    
    ## -- 07 -- ##
    fallback = remain[remain['ent_quote_dif_parag_dist'] <= K] 
    fallback = fallback.assign(entity_final = fallback['entity_dist'],
                                         crit_entity_final = 7)    
                
    ## -- 08 -- ##                         
    undefined = remain[remain['ent_quote_dif_parag_dist'] > K]
    undefined = undefined.assign(entity_final = 'undefined',
                                         crit_entity_final = 8)
    
    
    df = pd.concat([stronger_crit, 
                    sec_stronger_crit, 
                    third_stronger_crit, 
                    forth_stronger_crit,
                    fifth_stronger_crit,
                    sixth_stronger_crit, 
                    fallback,
                    undefined],           # Rbind DataFrames
                    ignore_index = True,
                    sort = False)
    
    df = df.sort_values(['id_pair'], ascending = [True]) 
    
    return df


