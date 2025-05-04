## Grade Summary (Group): 

- Quality of Planning Document: 78
- Quality of Requirements (in Kanban): 85

Combined Grade: 82

## Planning Document Feedback (Group): 

- Your system description should be 'in your own words.' These words look like my words! :)
- The architectural overview should (1) 'describe the design/architecture of your system', (2) 'include a list of all major system components', and (3) 'include a system diagram'. You only did the last of these, which was a copy of my diagram from the project description, and it includes everything (both front- end and back- end components). At the very least you should indicate which part of the architecture you are working on.
- You didn't list any epics. Epics are large user stories. You just pasted my functional and non-functional requirements. You need to distill those into large user stories that capture the big features you need to implement.
- Your technologies list looks very reasonable. Listing Python as the core programming language and the 'requests' package of Python for API calls would have been good to list as well.
- The formatting on your MVP could be better, but at least you did exclude some of the possible features. It looks like you removed 'Generate Usage Reports' and 'Equipment Status Verification on Returns', which is pretty reasonable.
- Your roadmap looks ok. I like that you included integration with the Checkpoint API team explicitly in your roadmap. I suspect you are going to need multiple integration points though. In sprints 3- 5 you will likely need to consume some new resources from them to support each of the pages you build out. For example, since you are creating the admin controls page in sprint 4, there is a good chance you won't be able to integrate with the back- end for that functionality until Sprint 5.
- Update your planning document based on my comments above, and I'll give you some points back.

## Requirements Feedback (Group): 

- Your user stories are decent (and occasionally funny). One suggestion. Many of your user stories can be broken up into lots of other stories. You can probably divide up US10 into a dozen stories :)
- Your titles are consistently formatted, but very difficult to understand at times. The relationship between US5 and US6 is confusing, and US6 really needs to be broken up further. When you see 10+ hours on a single story, it's time to start chopping it up.
- You need to link your stories to epics, so they are traceable.
- You have acceptance criteria on all of your user stories, and it is generally pretty good.
- You've made an attempt at estimating your stories. If you are going to use ranges of hours, I recommend shifting the ranges down a bit or add some additional buckets. You are basically using a 'small', 'medium', and 'large' scale right now. But your 'small' is a huge range. I think something like 'less than 2 hours' for small would be more reasonable. 5 hours is a decent sized chunk of work given your capacities per sprint.
- Your stories look prioritized in the order of your road map, which is great. I am still wondering why check- in/check- out functionality are all the way out in sprint 5. Something we should discuss.
