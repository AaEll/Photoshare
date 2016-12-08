CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    user_id INT4 AUTO_INCREMENT,
    first_name VARCHAR(255), 
    last_name VARCHAR(255), 
    DOB DATE, 
    hometown VARCHAR(255), 
    gender ENUM('F', 'M', ''), 
    email varchar(255) UNIQUE,
    password varchar(255),
  CONSTRAINT users_pk PRIMARY KEY (user_id)
);

CREATE TABLE Friends_of (
  user_id INT4,
  user_id_friend INT4,
  CONSTRAINT friends_of_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Album
(
  album_title VARCHAR(255), 
  album_id INT4 AUTO_INCREMENT PRIMARY KEY NOT NULL,
  user_id INT NOT NULL,
  date_of_creation DATE,
  CONSTRAINT album_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Pictures
(
  picture_id int4  AUTO_INCREMENT,
  user_id int4,
  imgdata longblob,
  caption VARCHAR(255),
  album_id INT4,
  INDEX upid_idx (user_id),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  CONSTRAINT album_pix_fk FOREIGN KEY (album_id) REFERENCES Album(album_id)
);

CREATE TABLE Liked_pictures 
(
  picture_id int4, 
  user_id int4,
  CONSTRAINT liked_picture_id_fk FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id),
  CONSTRAINT liked_user_id_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);


CREATE TABLE Tagged_Photos
(
  word VARCHAR(20), 
  picture_id INT NOT NULL,
  CONSTRAINT tagged_fk FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);

CREATE TABLE Comment
(
  comment_id INT4 NOT NULL PRIMARY KEY AUTO_INCREMENT, 
  user_id INT NOT NULL, 
  text VARCHAR(60000), 
  date DATE,
  CONSTRAINT comment_fk FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE Commented_photos 
(
   comment_id INT4,
   picture_id INT4,
   CONSTRAINT comment_photo_fk FOREIGN KEY (comment_id) REFERENCES Comment(comment_id),
   CONSTRAINT comment_photo_fk_2 FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id)
);


INSERT INTO Users(user_id, first_name, last_name)  VALUES(-1, "Anonymous", "");





