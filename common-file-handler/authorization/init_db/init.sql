CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
	id SERIAL PRIMARY KEY ,
	user_name VARCHAR (255) UNIQUE NOT NULL,
	default_directory VARCHAR (255),
	hashed_password VARCHAR (255) NOT NULL,
	api_key VARCHAR (255) NOT NULL,
	email VARCHAR (255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
	id UUID NOT NULL DEFAULT uuid_generate_v4() PRIMARY KEY,
	file_path VARCHAR (255) NOT NULL,
	file_size VARCHAR (255),
	file_creation_time VARCHAR (255) NOT NULL,
	file_content VARCHAR (255) NOT NULL,
	file_name VARCHAR (255) NOT NULL,
	full_path VARCHAR (255) NOT NULL,
	original_name VARCHAR (255) NOT NULL,
    additional_info JSON

);

CREATE TABLE IF NOT EXISTS streaming_files (
    id UUID NOT NULL DEFAULT uuid_generate_v4() PRIMARY KEY,
    file_temp_path VARCHAR (255) NOT NULL,
    file_id VARCHAR (255),
    file_creation_time VARCHAR (255) NOT NULL

);

ALTER TABLE IF EXISTS public.files ADD COLUMN IF NOT EXISTS additional_info json;