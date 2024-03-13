-- Schema

CREATE TABLE room (
number TEXT PRIMARY KEY,
capacity INT);

CREATE TABLE course (
number TEXT PRIMARY KEY,
title TEXT,
room TEXT,
FOREIGN KEY (room) REFERENCES room(number));

CREATE TABLE department (
name TEXT PRIMARY KEY,
office TEXT);

CREATE TABLE student (
id INT PRIMARY KEY,
name TEXT);

CREATE TABLE enrolled (
student INT,
course TEXT,
PRIMARY KEY (student, course),
FOREIGN KEY (student) REFERENCES student(id),
FOREIGN KEY (course) REFERENCES course(number));

CREATE TABLE majors_in (
student INT,
dept TEXT,
PRIMARY KEY (student, dept),
FOREIGN KEY (student) REFERENCES student(id),
FOREIGN KEY (dept) REFERENCES department(name));


-- Records

INSERT INTO room (number, capacity) VALUES ('MACD 117', 60);
INSERT INTO room (number, capacity) VALUES ('MACD 104', 30);
INSERT INTO room (number, capacity) VALUES ('BP 316', 25);
INSERT INTO room (number, capacity) VALUES ('BP 326', 25);
INSERT INTO room (number, capacity) VALUES ('BP 327', 2);

INSERT INTO course (number, title, room) VALUES ('CSCI 120', 'Introduction to Computing', 'MACD 117');
INSERT INTO course (number, title, room) VALUES ('CSCI 127', 'Basics of Software Design and Emerging Technology', 'MACD 104');
INSERT INTO course (number, title, room) VALUES ('CSCI 220', 'Database Management and Systems Design', 'MACD 117');
INSERT INTO course (number, title, room) VALUES ('MATH 120', 'Calculus I', 'BP 316');
INSERT INTO course (number, title, room) VALUES ('MATH 121', 'Calculus II', 'BP 326');

INSERT INTO department (name, office) VALUES ('CSCI', 'MACD TODO');
INSERT INTO department (name, office) VALUES ('MATH', 'BP 327');

INSERT INTO student (id, name) VALUES (1, 'Adrian Smith');
INSERT INTO student (id, name) VALUES (2, 'Albert Holmes');
INSERT INTO student (id, name) VALUES (3, 'Allison Jenkins');
INSERT INTO student (id, name) VALUES (4, 'Julie Huffman');
INSERT INTO student (id, name) VALUES (5, 'Joyce Anderson');
INSERT INTO student (id, name) VALUES (6, 'Joshua Wright');

INSERT INTO majors_in (student, dept) VALUES (1, 'CSCI');
INSERT INTO majors_in (student, dept) VALUES (3, 'MATH');
INSERT INTO majors_in (student, dept) VALUES (4, 'CSCI');

INSERT INTO enrolled (student, course) VALUES (1, 'CSCI 120');
INSERT INTO enrolled (student, course) VALUES (2, 'CSCI 120');
INSERT INTO enrolled (student, course) VALUES (3, 'MATH 121');
