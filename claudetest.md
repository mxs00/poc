# Project Overview

## Architecture
- **Database**: PostgreSQL without ORM only native sql

## Database Schema Notes
- table names need to be prefixed with tbl_
- key column names need to be prefixed with table acronym 
- add audit columns
- maintain referential integrity
- foreign keys are prefixed with the table acronym
- use varchar for keys, do not use UUID datatype

====
prompts:
create a postgres database schema to manage llm pipelines to handle the pipeline steps can be sequential,parallel,start,end. 
each step needs to have reference to next and previous step in pipeline, maintain steps relationship in seperate table
create pipeline definition tables
create pipeline runtime execution tables

 chats, sessions, messages, conversations. 

the schema needs to have referencial integrity, 
table names need to be prefixed with tbl_
all keys need to be prefixed with table acronym 


create readme.md file
