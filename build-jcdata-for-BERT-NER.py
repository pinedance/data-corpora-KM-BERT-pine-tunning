# -*- coding: utf-8 -*-
"""
fine_tune_BERT_한문_자동표점_데이터준비.ipynb
Original file is located at
    https://colab.research.google.com/drive/1JDW5AdlGX3hD9I9wVl6mYFhmRDECl-ST
"""

# %%
import regex as re
from collections import Counter, ChainMap
from os import path
import json
import requests

#%%
# bash download-jcdata.sh

#%%
IMPORT_DIR = path.join("rawdata")
EXPORT_DIR = path.join("export", "jcdata")
config = dict()

# %%
TEXT_LEN_MIN = 5
TEXT_LEN_MAX = 512 - 4

# %%
with open( path.join( IMPORT_DIR, "books.html"), "r", encoding="UTF-8-sig") as fl:
    bookhtml = fl.read()

# %%
RE_HEADER = re.compile(r'<header.+?/header>', flags=re.DOTALL )
RE_TAG = re.compile(r'<.*?>')

# %%
def cleanhtml( raw_html ):
    text = re.sub( RE_HEADER, "", raw_html )
    text = re.sub( RE_TAG, "", text )
    text = re.sub( r'\r\n', '\n', text)
    text = re.sub( r'\n+', '\n', text )
    return text.strip()

#%%
char_dup_req = requests.get("https://kmapibox.mediclassics.kr/api/tn/dict/duplications?type=json", verify=False)
char_var_custom_req = requests.get("https://kmapibox.mediclassics.kr/api/tn/dict/customvariants?type=json", verify=False)
char_var_ext_req = requests.get("https://kmapibox.mediclassics.kr/api/tn/dict/customvariantsExtention?type=json", verify=False)

#%%
CHAR_DUP_SETS = char_dup_req.json()
CHAR_VAR_CUSTOM_SETS = char_var_custom_req.json()
CHAR_VAR_EXT_SETS = char_var_ext_req.json()

#%%
CHAR_DUP_TABLE = ChainMap( *[ str.maketrans(a, b) for a, b in CHAR_DUP_SETS ] ) 
CHAR_VAR_CUSTOM_TABLE = ChainMap( *[ str.maketrans(a, b) for a, b in CHAR_VAR_CUSTOM_SETS ]) 
CHAR_VAR_EXT_TABLE = ChainMap( *[ str.maketrans(a, b) for a, b in CHAR_VAR_EXT_SETS ]) 
CHAR_ALL_TABLE = dict( ChainMap( CHAR_DUP_TABLE, CHAR_VAR_CUSTOM_TABLE, CHAR_VAR_EXT_TABLE ))

#%%
def cleanchar( text ):
    text_ = text + ""
    text_ = text_.translate( CHAR_ALL_TABLE )
    # for a, b in CHAR_DUP_SETS:
    #     text_ = text_.replace(a, b)
    # for a, b in CHAR_VAR_CUSTOM_SETS:
    #     text_ = text_.replace(a, b)
    # for a, b in CHAR_VAR_EXT_SETS:
    #     text_ = text_.replace(a, b)
    return text_

# %%
booktext_ = cleanhtml( bookhtml )
booktext_ = cleanchar( booktext_ )
print( booktext_[0:100] )

#%%
# https://huggingface.co/raynardj/classical-chinese-punctuation-guwen-biaodian/blob/main/config.json
old_id2label = {
    "0": "O",
    "1": "\u3002",
    "2": "\uff0c",
    "3": "\uff1a",
    "4": "\uff1b",
    "5": "\uff1f",
    "6": "\uff01",
    "7": "\"",
    "8": "\"",
    "9": "'",
    "10": "'",
    "11": "\uff08",
    "12": "\uff09",
    "13": "\"",
    "14": "\"",
    "15": "\uff08",
    "16": "\uff09",
    "17": "\u3010",
    "18": "\u3011",
    "19": "\u3010",
    "20": "\u3011"
}

#%%
old_label_list = list( old_id2label.values() )
new_label = [
    # "、", 
    # "《", "》"
]
new_label_list = old_label_list + new_label
id2label = { str(k):v for k,v in enumerate(new_label_list) }
config["id2label"] = id2label 
config["label2id"] = {
    "\"": 14,
    "'": 10,
    "O": 0,
    "\u3002": 1,
    "\u3010": 19,
    "\u3011": 20,
    "\uff01": 6,
    "\uff08": 15,
    "\uff09": 16,
    "\uff0c": 2,
    "\uff1a": 3,
    "\uff1b": 4,
    "\uff1f": 5
    # "、": 21,
    # "《": 22, 
    # "》": 23
},

# %%
replace_set = [
    # ("O", ""), 
    ("(", "（"), (")", "）"),
    (":", "："), (";", "；"),
    ("!", "！"), ("?", "？"),
    ("[", "〔"), ("]", "〕"), 
    ("『", '"'), ("』", '"'),
    ("「", "'"), ("」", "'"),
]
for a, b in replace_set:
    booktext_ = booktext_.replace(a,b)

booktext = booktext_

# %%
char_exhan = Counter( re.findall(r'[^\p{Han}]', booktext ) )
print( char_exhan.most_common(100) )


#%%
for k in id2label.values():
    print( k, char_exhan[k] )

#%%
punc_list = list( sorted( set( id2label.values() ) ) )
re_punc_raw = '[' + ''.join( punc_list ) + ']'
RE_PUNC = re.compile( re_punc_raw )

punc_list_not_O = punc_list.copy()
punc_list_not_O.remove("O")
re_punc_not_O_raw = '[' + ''.join( punc_list_not_O ) + ']'
RE_PUNC_NOT_O = re.compile( re_punc_not_O_raw )

print( punc_list )

#%%
puncs_lg_2 = Counter( re.findall( re.compile( '[' + ''.join( punc_list_not_O ) + ']+' ), booktext )  )
print( puncs_lg_2 )

#%%
def filter_booklines( raw_booklines ):
    rst1 = list()
    for line in raw_booklines:
        if len(line) < TEXT_LEN_MAX:
            rst1.append( line.strip() )
        else:
            raw_lines_shorten = line.split("。")
            lines_shorten = [ l.strip() + "。" for l in raw_lines_shorten ]
            rst1.extend( lines_shorten )

    rst2 = list()
    for line in rst1:
        if len( line.strip() ) == 0: # space line
            continue
        if len(line) < TEXT_LEN_MIN:
            continue
        if len(line) > TEXT_LEN_MAX:
            continue
        rst2.append( line )

    return rst2

#%%
raw_booklines = re.split(r'\n+', booktext )
org_booklines = filter_booklines(  raw_booklines )
len( org_booklines )

#%%
def divide_bookline( org_bookline ):
    l1 = list( org_bookline + "" )
    l2 = list( org_bookline[1:] ) + ["<END>"]
    r1, r2 = list(), list()
    for a, b in list( zip( l1, l2 ) ):
        if a in punc_list_not_O:
            continue
        else:
            if b == "<END>":
                r1.append( a )
                r2.append( "O" )
            elif b not in punc_list_not_O:
                r1.append( a )
                r2.append( "O" )
            elif b in punc_list:
                r1.append( a )
                r2.append( b )

    return "".join(r1), "".join(r2)

# %%
# test
t = 2223
tg = org_booklines[ t ]
tg1, tg2 = divide_bookline( tg )
print( tg )
print( tg1, len(tg1) )
print( tg2, len(tg2) )

#%%
FILE_SIZE = 300000
N_FILES = int( len( org_booklines ) / FILE_SIZE ) + 1

# %%
file_list = open( path.join( EXPORT_DIR, "filelist.txt"), "w", encoding="UTF-8") 
file_handlers = list()
for i in range( N_FILES ):
    tail_n = '_{:03d}'.format( i+1 )
    
    org_name = "org" + tail_n + ".txt"
    src_name = "src" + tail_n + ".txt"
    tgt_name = "tgt" + tail_n + ".txt"
    
    org_fl = open( path.join( EXPORT_DIR, org_name), "w", encoding="UTF-8")
    src_fl = open( path.join( EXPORT_DIR, src_name), "w", encoding="UTF-8")
    tgt_fl = open( path.join( EXPORT_DIR, tgt_name), "w", encoding="UTF-8")
    
    file_handlers.append( {"org": org_fl, "src": src_fl, "tgt": tgt_fl} )
    
    file_list.write( org_name + "\n")
    file_list.write( src_name + "\n")
    file_list.write( tgt_name + "\n")
    
file_list.close()

# %%

for i, line in enumerate( org_booklines ):
    file_idx = int( i / FILE_SIZE )
    line_src, line_tgt = divide_bookline( line )
    if len(line_src) != len( line_tgt ):
        print( line )
        print( line_src, len( line_src ))
        print( line_tgt, len(line_tgt))
    else:
        file_handlers[file_idx]["org"].write( line + "\n" )
        file_handlers[file_idx]["src"].write( line_src + "\n" )
        file_handlers[file_idx]["tgt"].write( line_tgt + "\n" )

#%%
for e in file_handlers:
    e["org"].close()
    e["src"].close()
    e["tgt"].close()

# %%
with open( path.join(EXPORT_DIR, "config.json"), "w", encoding="UTF-8") as fl:
    json.dump(config, fl, ensure_ascii = False) 
# %%
