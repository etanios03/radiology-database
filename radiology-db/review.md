Who Reviewed: Clarice Kim, May 20th 2026
Files reviewed: views.py, models.py, forms.py

Git hash: 5ebe9b79d9081b495083b9adbc597a35f73bbd9d

Questions to focus on:
1. Is the code in views.py readable, and would it benefit from being separated out? How would you do so?
Great start! Perhaps any sub element, such as a table or button could be separated out into different files. It seems then you could easily import the function and so the migration (hopefully) won't be too much work. You could also put all the "create_" functions in one file and "make_" functions in another.
2. Do the web pages and overall flow of uploading data work visually? How would you update the UI?
Yes - the flow works very well and it intuitive. In terms of viewing an image, perhaps you could replace the link with something along the lines of "view <filename>"? Or alternatively, you could provide a hint at the top of the table that users can click on the link to see metadata and calculate legion segmentation. 

Finally, you could apply styling via a styles.css file, perhaps changing font / background color to start. 

3. Do you have any tips for the html? 

Not particularly except for the styling with style.css mentioned earlier. 

Code Discussion:
- style pages and overall organization would benefit from more color, larger text, and more interactive parts of the webpage

- clearer organization of tables and connections between tables 

Changes in Code: 
This review has led me to think much more about style and code organization. I hadn't considered CSS before this review, and will now be exploring this in addition to templates and html files. Additionally, I am splitting my code into various files to ensure that it becomes more readable and modular for future updates.  