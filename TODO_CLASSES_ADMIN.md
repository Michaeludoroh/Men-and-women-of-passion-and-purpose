# Admin Classes Management Implementation Tracker

## Approved Plan Steps (Completed: [ ] → [x])

**Step 1: Update admin_routes.py** [x]
- Add imports: Course, Assignment, CourseForm, AssignmentForm
- Add /admin/classes GET/POST route
- Add /admin/classes/<id>/delete POST
- Add /admin/assignments GET/POST route  
- Add /admin/assignments/<id>/delete POST
- Update admin_dashboard stats

**Step 2: Update admin_dashboard.html** [x]
- Add courses/assignments stats cards
- Add Manage Classes/Assignments links

**Step 3: Create manage_classes.html** [x]
- List courses table + create form + deletes

**Step 4: Create manage_assignments.html** [x]
- List assignments (with course) + create form + deletes

**Step 5: Test** [ ]
- cd ministry_project &amp;&amp; python run.py
- Admin /admin/ → new features work (create/list/delete)
- Check DB/logs for errors

**Step 6: Cleanup & Complete** [ ]
- Update main TODO.md
- attempt_completion

Current: Step 1 next.

