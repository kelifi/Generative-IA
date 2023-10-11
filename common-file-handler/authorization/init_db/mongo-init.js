db.createUser(
        {
            user: "haythem",
            pwd: "root",
            roles: [
                {
                    role: "readWrite",
                    db: "file_handler"
                }
            ]
        }
);