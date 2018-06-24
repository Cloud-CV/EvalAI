teams_list = """
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "created_by": "admin",
            "id": 22,
            "members": [
                {
                    "member_id": 4,
                    "member_name": "admin",
                    "status": "Self"
                }
            ],
            "team_name": "OASIS"
        },
        {
            "created_by": "admin",
            "id": 55,
            "members": [
                {
                    "member_id": 4,
                    "member_name": "admin",
                    "status": "Self"
                }
            ],
            "team_name": "ROSES"
        }
    ]
}
"""


create_team = """
{
    "created_by": "admin",
    "id": 56,
    "team_name": "TestTeam"
}
"""


object_error = """
{
    "error": "Sorry, the object does not exist."
}
"""


participant_team_already_exists_error = """
{
    "team_name": ["participant team with this team name already exists."]
}
"""
