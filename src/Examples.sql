-------------------------
-- WELCOME TO LUCK
-------------------------
-- On this page you will find some examples and typologies 
-- to get the most out of Luck

-------------------------
-- Types of comments
-------------------------
-- Simple comment
--# Super comment
--#1 Super comment with color 1
--#2 Super comment with color 2
--#3 Super comment with color 3
--#4 Super comment with color 4
--#5 Super comment with color 5
--#6 Super comment with color 6
--#7 Super comment with color 7
--#8 Super comment with color 8
--#9 Super comment with color 9
--#10 Super comment with color 10
--#11 Super comment with color 10

-------------------------
-- Insert block section
-------------------------
--You can move between sections by pressing Ctrl+Q or Ctrl+W
--#- New Block

--#- New Block

--#- New Block

-------------------------
-- Query format
-------------------------
-- Commands and operators are automatically formatted, respecting color and 
-- capitalization according to the user's selected customization.

-- Parameters can be entered using the format {parameter_example}

-- To run a query one by one, you can right-click and select "Run"" or press F9.
-- To run all queries, you can right-click and select "Run all" or press F10.

-- Remember to select your preconfigured dsn in the SQL menu

drop DATABASE IF EXISTS examples cascade
;

CREATE DATABASE IF NOT EXISTS examples COMMENT 'Example data for Luck';
;

show databases
;

show tables in examples
;

DROP table IF EXISTS examples.{parameter_example} purge
;

CREATE TABLE IF NOT EXISTS examples.{parameter_example} (
    -- Integers
    col_tinyint TINYINT,
    col_smallint SMALLINT,
    col_int INT,
    col_bigint BIGINT,
    
    -- Floating point & Fixed point
    col_float FLOAT,
    col_double DOUBLE,
    col_decimal DECIMAL(18,2),
    
    -- String & Character (UTF-8)
    col_string STRING,
    col_varchar VARCHAR(255),
    col_char CHAR(10),
    
    -- Date & Time
    col_timestamp TIMESTAMP,
    col_date TIMESTAMP,
    
    -- Boolean
    col_boolean BOOLEAN
)
STORED AS PARQUET
;

INSERT INTO TABLE examples.{parameter_example} VALUES
(1, 10, 1001, 100000, 10.5, 5000.50, 1250.75, 'Alice Smith', CAST('Sales Dept' AS VARCHAR(255)), CAST('PERM' AS CHAR(10)), '2023-01-15 08:30:00', '2023-01-15', true),
(2, 20, 1002, 200000, 12.0, 6200.00, 2100.50, 'Bob Johnson', CAST('IT Support' AS VARCHAR(255)), CAST('TEMP' AS CHAR(10)), '2023-02-10 09:00:00', '2023-02-10', true),
(3, 30, 1003, 300000, 15.5, 7500.25, 3400.00, 'Charlie Brown', CAST('Marketing' AS VARCHAR(255)), CAST('PERM' AS CHAR(10)), '2023-03-05 10:15:00', '2023-03-05', false),
(4, 40, 1004, 400000, 9.8, 4800.75, 950.25, 'Diana Prince', CAST('Finance' AS VARCHAR(255)), CAST('PERM' AS CHAR(10)), '2023-04-20 11:00:00', '2023-04-20', true),
(5, 50, 1005, 500000, 22.1, 8900.00, 4200.80, 'Edward Norton', CAST('Legal' AS VARCHAR(255)), CAST('EXEC' AS CHAR(10)), '2023-05-12 08:00:00', '2023-05-12', true),
(6, 60, 1006, 600000, 11.2, 5300.40, 1500.00, 'Fiona Glen', CAST('HR' AS VARCHAR(255)), CAST('TEMP' AS CHAR(10)), '2023-06-01 09:30:00', '2023-06-01', false),
(7, 70, 1007, 700000, 14.7, 6700.10, 2800.60, 'George King', CAST('Logistics' AS VARCHAR(255)), CAST('PERM' AS CHAR(10)), '2023-07-18 14:00:00', '2023-07-18', true),
(8, 80, 1008, 800000, 18.9, 7200.00, 3100.45, 'Hannah Abbott', CAST('R&D' AS VARCHAR(255)), CAST('PERM' AS CHAR(10)), '2023-08-25 16:45:00', '2023-08-25', true),
(9, 90, 1009, 900000, 13.4, 5900.85, 1900.20, 'Ian Wright', CAST('Security' AS VARCHAR(255)), CAST('TEMP' AS CHAR(10)), '2023-09-30 22:00:00', '2023-09-30', false),
(10, 100, 1010, 1000000, 25.0, 9500.00, 5000.00, 'Jenny Lane', CAST('Executive' AS VARCHAR(255)), CAST('EXEC' AS CHAR(10)), '2023-10-05 07:15:00', '2023-10-05', true);
;

select * from examples.{parameter_example}
;

select * from examples.table_that_does_not_exist
;
