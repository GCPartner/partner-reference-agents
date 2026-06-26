CREATE TABLE IF NOT EXISTS daily_sales (
    sales_date DATE,
    location VARCHAR(255),
    product_line VARCHAR(255),
    sales_amount NUMERIC,
    PRIMARY KEY (sales_date, location, product_line)
);
