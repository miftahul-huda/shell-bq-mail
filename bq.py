import sys, getopt
import argparse
from dotenv import load_dotenv
import os
from google.cloud import bigquery
from google.api_core.exceptions import BadRequest
import datetime
import re



def main():

    load_dotenv()

    parser = argparse.ArgumentParser(
                    prog = 'BQ Runner',
                    description = 'Run query against BigQuery',
                    epilog = 'Devoteam')

    parser.add_argument('-q', '--query', help='The query to be executed', required=True)
    parser.add_argument('-s', '--start', help='The start number of query to be executed', required=False)  
    args = parser.parse_args()

    if(args.start == None):
        args.start = 1

    now = datetime.datetime.now()
    print("Start running BQ scripts at " + str(now))
    bqrun(args.query, int(args.start))

    now = datetime.datetime.now()
    print("\n\nFinished running BQ scripts at " + str(now))

def set_declare(query, declares, sets):
    #print(declares)
    #print(sets)
    addedDeclares = []
    addedSets = []
    decs = ""
    sets2 = ""
    for declare in declares:
        regex = "declare\s+([A-Za-z0-9_]+)\s+"
        variables = re.findall(regex, declare, re.IGNORECASE)
        if(len(variables) > 0):
            variable = variables[0]
            if(variable in query and declare not in addedDeclares):
                decs += declare + ";\n"
                addedDeclares.append(declare)


    for set in sets:
        regex = "set\s+([A-Za-z0-9_]+)\s+"
        variables = re.findall(regex, set, re.IGNORECASE)
        if(len(variables) > 0):
            variable = variables[0]
            if(variable in query and set not in addedSets):
                sets2 += set + ";\n"
                addedSets.append(set)

    query = decs + "" + sets2 + "" + query
    return query        

def get_declare(query):
    regex = "(declare\s+[A-Za-z0-9_]+\s+\w+)"
    declares = re.findall(regex, query, re.IGNORECASE)
    if(len(declares) > 0):
        return declares[0]
    else:
        return ""
    
def get_set(query):
    regex = "(set\s+[A-Za-z0-9_]+\s*=[\S\n\t\v ]*)"
    sets = re.findall(regex, query, re.IGNORECASE)
    if(len(sets) > 0):
        return sets[0]
    else:
        return ""
    
def bqrun(q, start):
    # to store declare and set queries
    declares = []
    sets = []

    # flag to run query. Don't run declare and set query.
    run_query = True

    # Construct a BigQuery client object.
    client = bigquery.Client(project=os.environ["gcp_project"])
    counter = 1
    queries = q.split(";")
    results = ""
    for query in queries:
        run_query = True
        if(query != None and len(query.strip()) > 0):
            if(counter >= start):
                query = query.strip()
                #print ("query raw")
                #print (query)
                try:

                    if(query.lower().find("declare") != -1):
                        declare = get_declare(query)
                        if(not declare in declares):
                            declares.append(declare)
                        run_query = False
                    if(query.lower().find("set") != -1):
                        #sset = get_set(query)
                        sset = query
                        if(not sset in sets):
                            sets.append(sset)
                        run_query = False
                    
                    if(run_query):
                       
                        print("======================================================")
                        query = set_declare(query, declares, sets)
                        print("Query #{}:".format(counter))
                        print(query + "...")

                        #if(query != None and "select" in query.lower()):
                        #    print("\n======================================================\n" + query + "\n======================================================\n")
                        
                        
                        job_config = bigquery.QueryJobConfig(
                            # Run at batch priority, which won't count toward concurrent rate limit.
                            priority=bigquery.QueryPriority.BATCH
                        )


                        now1 = datetime.datetime.now()
                        results = client.query(query, job_config)  # Make an API request.
                        rows = results.result()  # Waits for query to finish
                        now2 = datetime.datetime.now()

                        t = now2 - now1
                        print("\nQuery is succesful and it took " + str(t) + " to complete.")

                        
                        # Print the query result if the qeuery is a SELECT query.
                        try:
                            selectIdx = query.lower().strip().find("select")
                            if(selectIdx == 0):  
                                print("The query result:")
                                #print(results._query_results._properties['schema']['fields'])
                                fields  = results._query_results._properties['schema']['fields']
                                fieldnames = ""
                                for field in fields:
                                    fieldnames += field['name'] + "\t|"

                                if(len(fieldnames) > 0):
                                    fieldnames = fieldnames[0:len(fieldnames) -1]
                                print (fieldnames)

                                rowline = ""
                                for row in rows:
                                    # Row values can be accessed by field name or index.
                                    for f in fields:
                                        rowline += str(row[f['name']]) + "\t"                    
                                    print(rowline)
                                    rowline = ""
                            

                                #print ("---Done bq.py Run query----")
                            else:
                                print("No Row Result")

                        except:
                            print("No Row Result")

                        
                        print("======================================================")
                        
                    
                except BadRequest as e:
                    print("\n\nQuery Error, Query# {}".format(counter))
                    #print("\n===================Error Query===================================\n")
                    print (query)
                    #print("\n===================/Error Query===================================\n")
                    print("\nQuery error: {}".format(e.args[0]))
                    print("======================================================")
                except KeyboardInterrupt:
                    # quit
                    print("Keyboard interrupt... exiting...")
                    sys.exit()
                except:
                    print("\n\nQuery Error, Query# {}".format(counter))
                    #print("\n===================Error Query===================================\n")
                    print (query)
                    #print("\n===================/Error Query===================================\n")
                    if(isinstance(results, str) == False and results.errors != None):
                        print(results.errors)
                    print("======================================================")
            

            if(run_query): 
                counter = counter + 1



        #for row in results:
            
    print("---bq.py Run BQ srcipt done")

if __name__ == "__main__":
    main()



