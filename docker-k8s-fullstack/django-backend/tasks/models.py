from django.db import models


class Task(models.Model):
    title = models.CharField(max_length=200)
    done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tasks"
        ordering = ["-created_at"]

    def to_dict(self):
        # .NET backend-um idhe JSON shape thaan return pannum — frontend rendu backend-kum same
        return {
            "id": self.id,
            "title": self.title,
            "done": self.done,
            "createdAt": self.created_at.isoformat(),
        }
