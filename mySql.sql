
CREATE TABLE `product` (
  `pid` BIGINT AUTO_INCREMENT NOT NULL,
  `code` varchar(255) NOT NULL,
  `name` varchar(70) DEFAULT NULL,
  `image` varchar(255) NOT NULL,
  `category` varchar(70) DEFAULT NULL,
  `price` int(11) DEFAULT NULL,
  `discount` int(11) DEFAULT NULL,
  PRIMARY KEY (`pid`)
);

CREATE TABLE `shoppingHistory` (
  `user_id` BIGINT NOT NULL,
  `pid` BIGINT NOT NULL
);

ALTER TABLE shoppingHistory MODIFY user_id VARCHAR(100);
ALTER TABLE shoppingHistory MODIFY pid VARCHAR(100);


CREATE TABLE USERGRP (`user_id` BIGINT AUTO_INCREMENT, `user_name` VARCHAR(45) NULL, `user_username` VARCHAR(45) NULL, `user_password` VARCHAR(45) NULL, PRIMARY KEY (`user_id`));

ALTER TABLE shoppingHistory ADD created DATETIME;
ALTER TABLE shoppingHistory ADD prodname varchar(70);

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_createUser`( IN p_name VARCHAR(20), IN p_username VARCHAR(20), IN p_password VARCHAR(20)) BEGIN
if ( select exists (select 1 from USERGRP where user_username = p_username) ) THEN
select 'Username Exists !!';
    ELSE
        insert into USERGRP
        (
            user_name,
            user_username,
            user_password
        )
        values
        (
            p_name,
            p_username,
            p_password
        );
    END IF;
END$$
DELIMITER;


commit;


