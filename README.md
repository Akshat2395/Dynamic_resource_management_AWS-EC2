# Dynamic_resource_management_AWS-EC2

**Note- Please refer the documentation for more details.**

## Objective

This project exposes the following AWS technologies: EC2, RDS, S3, CloudWatch and Elastic Load Balancer (ELB).

This project extends the [Face_Mask_Detection_webapp](https://github.com/Akshat2395/Face_mask_Detection_AWS_web_app) into an elastic web application that can resize its worker pool on demand. The worker pool is the set of EC2 instances that run the face detection user-app.

An auto scaling algorithm was developed to smoothly add and terminate user instancesas per demand.


## Web-App Features

The manager app used by the manager controls the worker pool. 

* **Listing workers:** Manager is able to see a list of workers in real time. For each worker, two charts are displayed in the list:

  a. First chart, shows the total CPU utilization of the worker for the past 30 minutes with the resolution of 1 minute.
  
  b. Second chart, shows the rate of HTTP requests received by the worker in each minute for the past 30 minutes. The chart has the rate (HTTP requests per minute) on the y-axis     and time on the x-axis.
  
* Displays a chart on the main page, showing the number of workers in the past 30 minutes.

* Provides a link to the load balancer user-app entry URL.

* Manager can manually change the worker pool size in addition to automatic scaling. Parameters taken into consideration are:

  a. CPU threshold for growing and shrinking the worker pool (used in automatic mode)
  
  b. Ratio by which to expand or reduce the worker pool (used in automatic mode)
  
* KILL switch - A button that terminates all the worker instances and then stops the manager itself. It also deletes application data stored on the database as well as all images stored on S3.
