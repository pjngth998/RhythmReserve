from fastapi import FastAPI,  HTTPException
from pydantic import BaseModel
from datetime import date
from datetime import time
from code_yam import *
from fastapi.responses import RedirectResponse
import uvicorn

app = FastAPI()
system = ReserveSystem()


@app.get("/")
def root():
    return {"message": "Welcome to ReserveSystem API", "docs": "/docs"}

@app.post("/register")
def api_register(type : str, name : str, username : str, password : str, email : str, phone : str, birthday : date, membership : Membership):
    result = system.register(type,name,username,password,email,phone,birthday)
    if result:
        return result.id
    
@app.post("/login")
def api_login(username : str, password: str):
    return system.login(username,password)

@app.post("/logout")
def api_logout(username : str):
    return system.logout(username)

@app.post("/edit_info")
def api_edit_info(username : str, data : Enum, new_info):
    return system.edit_info(username,data,new_info)

@app.post("/change_password")
def api_change_password(username : str, old_password : str, n_password:str);
    return system.change_password(username,old_password,n_password)


@app.post("/checkin")
def api_checkin(customer_id: str, reserve_id: str):
    result = system.checkin(customer_id, reserve_id)
    if result != "CHECK-IN SUCCESSFULLY!":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}

@app.post("/select_eq")
def api_select_eq(customer_id : str, branch_id : str,room_id : str, eq_list : list[str]):
    result = system.select_eq(customer_id, branch_id, room_id,eq_list)
    if result != "Can Reserve Equipment - Add to Booking Successfully":
        raise HTTPException(status_code=404, detail=result)
    return {"message": result}


if __name__ == "__main__":
    uvicorn.run("api:app",host = "127.0.0.1",port=8000, reload = True)