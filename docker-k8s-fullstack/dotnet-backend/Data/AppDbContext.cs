using Microsoft.EntityFrameworkCore;
using TaskApi.Models;

namespace TaskApi.Data;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<TaskItem> Tasks => Set<TaskItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        var task = modelBuilder.Entity<TaskItem>();
        task.ToTable("tasks");
        task.Property(t => t.Title).HasMaxLength(TaskItem.TitleMaxLength).IsRequired();
    }
}
