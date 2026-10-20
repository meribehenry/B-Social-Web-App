# B-Social-Web-App Backend API

A robust REST API built to power the B-Social, social media platform. This service handles user authentication, profile management, and creating post, commenting, and also handle reactions to post and comments. B-Social is created to help me understand how the web works and how to apply different solutions in solving different types of problems. This version is different from the previous once, has it include a well thought through design, where success isn't the only thing tested but how failure could be handled. Also it involves a more optimised database query strategies, to prevent N+1 query at any level and improve query speed.

This version uses a signed upload instead of the backend handling files, the neccessary parameters is signed and the signature would be used by the frontend to upload the file. 

## 🚀 Features
*   **Secure Authentication:** JWT-based user login and registration.
*   **Profile Management:** Custom user profiles with secure image uploads and unique user name.
*   **Creating Post:** Endpoints to manage creating and editing of posts.
* **Commenting:** User can comment to any post and edit them if any mistake was made.
* **Reacting to Posts and Comments:** User can react to different posts and comments.
*   **Concurrency:** Multithreaded execution for background tasks and some file processing.

## 🛠 Tech Stack
*   **Language:** Python 3.13
*   **Framework:** Django Rest Framework (DRF)
*   **Authentication:** Django Rest Framework Simple JWT
*   **Background Worker:** Celery
*   **Caching:** Redis
*   **Queue:** Redis (later would be changed to RabbitMQ)
*   **Database:** SQLite + Django ORM (later would br changed to Postgres)
*   **Storage:** Cloudinary