# 📊 CourseMetricMaster

> Revolutionizing educational assessment using data analytics to align curriculum design with program objectives and improve student outcomes.

## 🔍 Overview

CourseMetricMaster is a web-based analytics platform for academic institutions. It helps analyze Course Outcomes (CO) and Program Outcomes (PO) using student performance data, assisting faculty and admins in making informed decisions to enhance learning.

## 🎯 Aim

To transform educational assessment by:
- Analyzing student performance across different evaluation components
- Aligning academic metrics with program objectives
- Helping institutions improve curriculum design and student success

## 🛠️ Key Features

- 👩‍🎓 **Faculty Module**: Upload student details and marks.
- 👨‍💻 **Admin Module**: Manage faculty data and oversee the database.
- ⚖️ **CO-PO Mapping Analysis**: Calculates the success of outcomes based on a threshold.
- 📊 **Visual Output Page**: Displays calculated CO percentages, university marks, and averages.
- 🔬 **Data Structuring**: Converts unstructured assessment data into structured insights.

## ✨ Advantages

- Informed decision-making
- Curriculum optimization
- Enhanced student performance
- Adaptable to any college or course (UG & PG)
- Converts raw data into actionable reports

## 💡 Algorithm

### Input:
- CO & PO mapping per subject
- Marks from tests, assignments, seminars, models
- Threshold value (Y/N)
- University marks

### Steps:
1. Collect CO-PO mapping from faculty
2. Collect marks data for each component
3. For each CO:
   - Calculate percentage: `(marks / max marks) * 100`
   - If percentage > threshold → mark as 'Y', else 'N'
4. Combine multiple tests/models and assignments/seminars
5. Add university marks
6. Compute total average percentage
7. Generate output page with all data points

## 🚀 Tech Stack

- **Backend**: Python
- **Framework**: Flask
- **Frontend**: HTML, CSS (basic)
- **Database**: SQL-based

### Why Flask?
Flask enables rapid prototyping, supports RESTful APIs, dynamic page rendering, and integrates well with data-handling libraries. Its modularity and community support make it a great choice for scalable academic applications.

## 📅 Modules

### Admin:
- Upload/manage faculty information
- Monitor overall database

### Faculty:
- Upload student info
- Enter internal and external marks

## 🙏 Thank You

CourseMetricMaster is a scalable, analytical tool to assist institutions in elevating the quality of education using simple, data-driven processes.
