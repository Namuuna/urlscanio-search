This program takes in input queries and generates html file to show the result URLs and screenshots. 

1. Input queries (assumption that query syntaxes are correct):
    -add queries in "queries.txt", separated by comma

2. To run program:
    >python -m venv ./env
    >source env/Scripts/activate
    >pip install -r requirements.txt
    >python urlscanio.py

3. Quota rate limit:
    -If rate limit quota is surpassed then the program will sleep until all the queries are finished running.
 Until then, user can still see the "output-<timestamp>.html" file for already executed queries and its results. 

4. Output:
    -Output html file will be generated in the /output folder. Users will be able to choose from dropdown any query that's been executed to see hte results. 

