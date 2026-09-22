Campus Ride – Azure Serverless University Transport Management

A cloud-based university transport management system built using Microsoft Azure Serverless Services. 
The application enables students to track their assigned buses in real time, drivers to share live locations, and administrators to manage transport operations through a centralized dashboard.

Live Website https://webapp-neeraj1-etbsbddefwaha8ga.southeastasia-01.azurewebsites.net/

Features
* Student, Driver, and Admin role-based login
* Real-time bus location tracking
* Driver live location updates
* Admin dashboard for managing students and buses
* Interactive bus tracking using Azure Maps
* Serverless REST APIs with Azure Functions
* CI/CD deployment using Azure DevOps YAML Pipelines


Tech Stack

 Category   Technologies                 
 ---------  ---------------------------- 
 Frontend  HTML, CSS, JavaScript        
 Backend   Python, Azure Functions      
 Database  Azure Cosmos DB              
 Maps      Azure Maps                   
 Cloud     Azure Web App                
 DevOps    Azure DevOps, YAML Pipelines 



Project Structure

CampusRide-Azure-Serverless/

├── backend/
│   ├── function_app.py
│   ├── host.json
│   ├── requirements.txt
│   ├── .funcignore
│   └── .gitignore
│
├── frontend/
│   ├── index.html
├── backend1.yml
├── frontend1.yml
└── README.md


System Architecture

1. Students log in and view their assigned bus with its live location.
2. Drivers start the bus and continuously update GPS coordinates.
3. Azure Functions process requests and update location data.
4. Azure Cosmos DB stores student, bus, and notification information.
5. Azure Maps displays the live bus position on the frontend.
6. Azure DevOps Pipelines automate deployment to Azure Web App and Azure Functions.



CI/CD

This repository includes two Azure DevOps pipeline files:

backend1.yml – Builds and deploys the Azure Functions backend.
frontend1.yml – Deploys the frontend to Azure Web App.

The pipelines automate dependency installation, build, and deployment using Azure DevOps service connections.





Prerequisites

* Python 3.11+
* Azure Functions Core Tools
* Azure Cosmos DB
* Azure CLI (optional)

Clone the Repository

  git clone https://github.com/kneerajk2005/Campus-ride-Azure-Serverless.git
  cd Campus-ride-Azure-Serverless

Install Backend Dependencies
 
  cd backend
  pip install -r requirements.txt


Configure the required Azure Application Settings before running the application.

 Security

This public repository "does not include":

* Azure Cosmos DB keys
* Azure Maps subscription keys
* Storage connection strings
* Deployment credentials

All sensitive values are securely managed through Azure Application Settings and Azure DevOps service connections.



Author

Neeraj Kumar
 
Sasidhar 

Integrated M.Tech in Computer Science and Engineering

Azure Cloud • Serverless • Backend Development
