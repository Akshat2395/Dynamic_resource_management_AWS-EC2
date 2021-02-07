from app import global_http
def http_inc():
    global_http.http+=1
    print(global_http.http)
    return(global_http.http)
def http_dec():
    global_http.http-=1
    return (global_http.http)