CREATE TABLE product_table (
    product_id STRING (20)   PRIMARY KEY,
    name       STRING (100)  NOT NULL,
    price      DOUBLE (5, 3) DEFAULT (100) 
                             NOT NULL,
    size       STRING (4)    NOT NULL
);


CREATE TABLE user_table (
    user_id  INTEGER     PRIMARY KEY,
    name     STRING (40) NOT NULL,
    age      INTEGER (2) NOT NULL,
    gender   STRING (1)  NOT NULL,
    email    STRING (40) NOT NULL,
    password STRING (20) NOT NULL
                         DEFAULT (123) 
);

CREATE TABLE cart_table (
    user_id    INTEGER       REFERENCES user_table (user_id),
    product_id STRING (20)   REFERENCES product_table (product_id),
    price      DOUBLE (5, 3) NOT NULL,
    quantity   INTEGER (2)   NOT NULL
                             DEFAULT (1),
    amount     DOUBLE (5, 3) NOT NULL,
	PRIMARY KEY (user_id, product_id)
);

CREATE TABLE order_table (
	order_id		INTEGER(20),	
    user_id    		INTEGER       REFERENCES user_table (user_id),
    product_id 		STRING (20)   REFERENCES product_table (product_id),
    price      		DOUBLE (5, 3) NOT NULL,
    quantity   		INTEGER (2)   NOT NULL
                             DEFAULT (1),
    amount     		DOUBLE (5, 3) NOT NULL,
	payment_status	STRING(20),
	order_status	STRING(20),
	return_flg		STRING(3),
	PRIMARY KEY (order_id, product_id)
);

CREATE TABLE return_table (
    user_id    		INTEGER       REFERENCES user_table (user_id),
    order_id    	INTEGER(20)   REFERENCES order_table (order_id),
    product_id 		STRING (20)   REFERENCES product_table (product_id),
    price      		DOUBLE (5, 3) NOT NULL,
    quantity   		INTEGER (2)   NOT NULL
                             DEFAULT (1),
    amount     		DOUBLE (5, 3) NOT NULL,
	return_status	STRING(20),
	PRIMARY KEY (order_id, product_id)
);
