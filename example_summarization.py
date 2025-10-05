"""Example: Agentic summarization workflow using delete_note tool.

This demonstrates how an AI agent can:
1. Read multiple related notes
2. Generate a consolidated summary
3. Store the summary as a new note
4. Delete the original notes to reduce clutter
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def summarize_notes_workflow():
    """Example workflow: Consolidate multiple notes into one."""
    
    # Start MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("🤖 Starting Agentic Summarization Workflow\n")
            
            # Step 1: Store sample notes (simulating existing notes)
            print("📝 Step 1: Creating sample notes...")
            notes_to_consolidate = [
                ("Python Learning", "AsyncIO Basics", 
                 "# AsyncIO Basics\n\nAsyncIO allows concurrent execution using async/await syntax."),
                ("Python Learning", "AsyncIO Tasks",
                 "# AsyncIO Tasks\n\nTasks are used to schedule coroutines concurrently."),
                ("Python Learning", "AsyncIO Event Loop",
                 "# Event Loop\n\nThe event loop is the core of every asyncio application."),
            ]
            
            for project, title, content in notes_to_consolidate:
                result = await session.call_tool("store_note", {
                    "project": project,
                    "title": title,
                    "content": content
                })
                print(f"  ✓ Created: {title}")
            
            # Step 2: Read all notes
            print("\n📖 Step 2: Reading notes to consolidate...")
            all_content = []
            for project, title, content in notes_to_consolidate:
                result = await session.call_tool("retrieve_note", {
                    "project": project,
                    "title": title
                })
                # In real workflow, parse the result to extract content
                all_content.append(content)
                print(f"  ✓ Read: {title}")
            
            # Step 3: Generate summary (simulated - in reality, use AI)
            print("\n🤖 Step 3: Generating consolidated summary...")
            summary = """# AsyncIO Complete Guide

## Overview
AsyncIO is Python's built-in library for writing concurrent code using async/await syntax.

## Key Concepts

### Event Loop
The event loop is the core of every asyncio application. It manages and distributes 
the execution of tasks.

### Async/Await
AsyncIO allows concurrent execution using async/await syntax, making it easy to write
non-blocking code.

### Tasks
Tasks are used to schedule coroutines concurrently. They provide a way to run multiple
operations in parallel.

## Usage
```python
import asyncio

async def main():
    task1 = asyncio.create_task(operation1())
    task2 = asyncio.create_task(operation2())
    await task1
    await task2

asyncio.run(main())
```

---
*This note consolidates: AsyncIO Basics, AsyncIO Tasks, AsyncIO Event Loop*
"""
            print("  ✓ Summary generated")
            
            # Step 4: Store consolidated summary
            print("\n💾 Step 4: Storing consolidated summary...")
            result = await session.call_tool("store_note", {
                "project": "Python Learning",
                "title": "AsyncIO Complete Guide",
                "content": summary
            })
            print(f"  ✓ {result}")
            
            # Step 5: Delete original notes (cleanup)
            print("\n🗑️  Step 5: Deleting original notes...")
            for project, title, _ in notes_to_consolidate:
                result = await session.call_tool("delete_note", {
                    "project": project,
                    "title": title
                })
                print(f"  ✓ Deleted: {title}")
            
            # Step 6: Verify results
            print("\n✅ Step 6: Verification...")
            result = await session.call_tool("list_notes", {
                "project": "Python Learning"
            })
            print(f"\nRemaining notes in project:\n{result}")
            
            print("\n🎉 Workflow complete!")
            print("\n📊 Summary:")
            print("  - Original notes: 3")
            print("  - Consolidated into: 1 summary note")
            print("  - Originals deleted: 3")
            print("  - Net reduction: 2 notes")


async def delete_duplicates_workflow():
    """Example workflow: Find and remove duplicate notes."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n🤖 Starting Duplicate Detection Workflow\n")
            
            # Create some notes with duplicates
            print("📝 Creating test notes (including duplicates)...")
            test_notes = [
                ("Testing", "Note 1", "Unique content A"),
                ("Testing", "Note 2", "Unique content B"),
                ("Testing", "Note 3", "Unique content A"),  # Duplicate of Note 1
            ]
            
            for project, title, content in test_notes:
                await session.call_tool("store_note", {
                    "project": project,
                    "title": title,
                    "content": content
                })
                print(f"  ✓ Created: {title}")
            
            # In a real implementation, you would:
            # 1. Read all notes and hash their content
            # 2. Identify duplicates
            # 3. Delete duplicates while keeping one copy
            
            print("\n🔍 Detecting duplicates...")
            print("  ⚠️ Found: 'Note 3' is duplicate of 'Note 1'")
            
            print("\n🗑️  Deleting duplicate...")
            result = await session.call_tool("delete_note", {
                "project": "Testing",
                "title": "Note 3"
            })
            print(f"  ✓ {result}")
            
            # Cleanup test notes
            await session.call_tool("delete_note", {"project": "Testing", "title": "Note 1"})
            await session.call_tool("delete_note", {"project": "Testing", "title": "Note 2"})
            
            print("\n✅ Duplicate detection complete!")


async def version_cleanup_workflow():
    """Example workflow: Keep only recent versions."""
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n🤖 Starting Version Cleanup Workflow\n")
            
            # Create multiple versions of a note
            print("📝 Creating multiple versions of a note...")
            for i in range(5):
                result = await session.call_tool("store_note", {
                    "project": "Maintenance",
                    "title": "Evolving Document",
                    "content": f"# Version {i+1}\n\nThis is version {i+1} of the document."
                })
                print(f"  ✓ Created version {i+1}")
                await asyncio.sleep(0.1)  # Small delay to ensure different timestamps
            
            print("\n🔍 In a full implementation, you would:")
            print("  1. List all versions of the note")
            print("  2. Sort by timestamp (newest first)")
            print("  3. Keep N latest versions")
            print("  4. Delete older versions")
            
            print("\n🗑️  For now, deleting all versions...")
            result = await session.call_tool("delete_note", {
                "project": "Maintenance",
                "title": "Evolving Document"
            })
            print(f"  ✓ {result}")
            
            print("\n✅ Version cleanup complete!")


async def main():
    """Run example workflows."""
    print("=" * 60)
    print("  AGENTIC WORKFLOWS WITH delete_note TOOL")
    print("=" * 60)
    
    # Run workflows
    await summarize_notes_workflow()
    await delete_duplicates_workflow()
    await version_cleanup_workflow()
    
    print("\n" + "=" * 60)
    print("  ALL WORKFLOWS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
