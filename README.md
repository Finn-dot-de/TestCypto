@startuml
skinparam shadowing false
skinparam BoxPadding 10

' Manuelles, sauberes Schwarz-Weiß-Theme
skinparam sequence {
    ArrowColor black
    LifeLineBorderColor black
    LifeLineBackgroundColor white
    ParticipantBorderColor black
    ParticipantBackgroundColor white
    BoxBackgroundColor white
    BoxBorderColor black
}
skinparam databaseBackgroundColor white
skinparam databaseBorderColor black

actor ":User" as user

box "Frontend (Java EE 7)"
participant ":Browser / UI" as ui
participant ":TotpController" as fe_ctrl
participant ":TotpApiService" as fe_api
end box

box "Backend (Spring Boot)"
participant ":TotpController (REST)" as be_ctrl
participant ":TotpService" as be_svc
end box

database ":Datenbank" as db

user -> ui : Gibt 6-stelligen OTP-Code ein
activate ui

ui -> fe_ctrl : verifyTotpCodeLogin(code)
activate fe_ctrl

' --- 1. Self-Call (Gibt einen Wert zurück) ---
fe_ctrl -> fe_ctrl : email = leseAusSession("pending_user")
activate fe_ctrl
fe_ctrl -->> fe_ctrl : email
deactivate fe_ctrl

fe_ctrl -> fe_api : validateCode(email, code)
activate fe_api

fe_api -> be_ctrl : HTTP POST /validate (ValidationRequest)
activate be_ctrl

be_ctrl -> be_svc : validateTotpCode(email, code)
activate be_svc

be_svc -> db : findByEmail(email)
activate db
db --> be_svc : TotpCredentials (Secret)
deactivate db

' --- 2. Self-Call (Gibt einen Wert zurück) ---
be_svc -> be_svc : Prüft Code gegen Secret
activate be_svc
be_svc -->> be_svc : isValid (boolean)
deactivate be_svc

' Fallunterscheidung
alt Code ist gültig
    be_svc --> be_ctrl : return jwtToken
    be_ctrl --> fe_api : HTTP 200 OK (Auth-Token / JWT)
    fe_api --> fe_ctrl : return token
    
    ' --- 3. Self-Call (void Methode, kein Text am Return-Pfeil) ---
    fe_ctrl -> fe_ctrl : set2faCompleted(true)\nrotateSessionId()\nspeichereApiToken(token)
    activate fe_ctrl
    fe_ctrl -->> fe_ctrl
    deactivate fe_ctrl
    
    fe_ctrl --> ui : Redirect zur Hauptseite
    ui --> user : Zeigt Hauptseite an

else Code ist ungültig
    be_svc --> be_ctrl : throw Exception / return false
    be_ctrl --> fe_api : HTTP 401 Unauthorized
    fe_api --> fe_ctrl : throw Exception / return false
    
    ' --- 4. Self-Call (void Methode, kein Text am Return-Pfeil) ---
    fe_ctrl -> fe_ctrl : addErrorMessage()
    activate fe_ctrl
    fe_ctrl -->> fe_ctrl
    deactivate fe_ctrl
    
    fe_ctrl --> ui : Seite neu laden mit Fehler
    ui --> user : Zeigt Fehlermeldung "Code falsch"
end

deactivate be_svc
deactivate be_ctrl
deactivate fe_api
deactivate fe_ctrl
deactivate ui

@enduml
