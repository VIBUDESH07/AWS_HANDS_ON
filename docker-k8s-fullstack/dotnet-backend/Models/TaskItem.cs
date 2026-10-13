namespace TaskApi.Models;

// "Task" nu peru vecha System.Threading.Tasks.Task-oda clash aagum, adhanala TaskItem
public class TaskItem
{
    public const int TitleMaxLength = 200;

    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public bool Done { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public record CreateTaskRequest(string Title);

// PATCH partial update — anuppaadha field-a maathakoodadhu, adhanala nullable
public record UpdateTaskRequest(string? Title, bool? Done);
