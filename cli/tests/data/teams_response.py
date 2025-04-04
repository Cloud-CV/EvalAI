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
            "team_name": "OASIS",
            "team_url": ""
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
            "team_name": "ROSES",
            "team_url": ""
        }
    ]
}
"""


host_teams = """
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "created_by": "participant",
            "id": 4,
            "members": [
                {
                    "id": 4,
                    "permissions": "Admin",
                    "status": "Self",
                    "team_name": 4,
                    "user": "participant"
                }
            ],
            "team_name": "Team1",
            "team_url": ""
        },
        {
            "created_by": "participant",
            "id": 5,
            "members": [
                {
                    "id": 5,
                    "permissions": "Admin",
                    "status": "Self",
                    "team_name": 5,
                    "user": "participant"
                }
            ],
            "team_name": "Team2",
            "team_url": ""
        },
        {
            "created_by": "participant",
            "id": 6,
            "members": [
                {
                    "id": 6,
                    "permissions": "Admin",
                    "status": "Self",
                    "team_name": 6,
                    "user": "participant"
                }
            ],
            "team_name": "Team3",
            "team_url": ""
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
