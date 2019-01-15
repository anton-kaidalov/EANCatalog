# EANCatalog

## Overview
Provides REST API with the following features:
* CRUD for products. Every product has five required fields: name, brand, category, price, EAN;
* EAN is validated as [EAN-13](https://en.wikipedia.org/wiki/International_Article_Number);
* CRUD for bulk_import_tasks, which are used for the importing of products from Google Sheets. The import process is asynchronous, buffered and cancellable.

## Google Sheet structure
The first row is skipped and is expected to contain headers for the user's convenience. The order of headers matters: name, brand, category, price, EAN.
EANs are expected as text. You can separate them with dashes arbirtarily (e.g. 0-000000-000000) or, without dashes, you need to start them with a single quote in the sheet, like this: '0000000000000.
Empty rows are allowed.

## Architecture
The solution consists of the three main components:
* REST API application itself, based on Eve (which is, in turn, based on Flask), backed by MongoDB. It is expected to process all requests quickly, delegating time-consuming tasks like bulk import to special workers;
* simple job queue manager, called python-rq and backed by Redis. It manages the job queues for the workers;
* worker class that accepts jobs, talks to Google Sheets and peforms the asynchronous importing.

## Installing, configuring
OS prerequisites:
* Unix/Linux (developed and tested on Ubuntu 18.04);
* Python 3;
* pipenv;
* mongodb;
* redis-server;
* (optional) httpie utility for issuing HTTP requests. Feel free to use curl or Postman.

Google prerequisites:
* you'll need to have an id of a Google Sheet with products data;
* the Google Sheet needs to be publicly accessible (for reading) by link;
* you'll also need to generate a Google API key under any developer's account (no matter whether it's the owner of the products Google Sheet or not). This key needs to be set in the file run.sh.

## Running
The simplest way of running the solution locally is using 3 command-line terminals:
* in the first terminal, you start run.sh (the REST API app);
* in the second terminal, you start run_rq.sh (the job queue manager);
* from the third terminal, you issue HTTP requests to the REST API. You can easily track the sequences of events in the other two terminals.

## Usage samples
The command-line utility httpie was used for submitting requests. Below you can find some command samples that demonstrate the major use cases.

Request the 5213<sup>th</sup> page of the products collection (GET is the default method):
```Batchfile
http :5000/products?page=5213
```

Create a task. It will be scheduled to be executed asynchronously, and will transition though statuses (Not started -> In progress -> ..., see source code).
```Batchfile
http post :5000/bulk_import_tasks sheet_id=<your sheet id>
```

Cancel the task with id 5c3d2c8f5648873425ce639a. Note that the valid [ETag](https://en.wikipedia.org/wiki/HTTP_ETag) value has to be provided as well:
```Batchfile
http patch :5000/bulk_import_tasks/5c3d2c8f5648873425ce639a status=Cancelled If-Match:e25a3e70e47134c7bcb84daa0521383931a4181d
```

## Project maturity
Although it's definitely not a quick-n-dirty PoC version, it's not a production-ready solution either. It's rather a working prototype, suitable for stakeholder demos, but not for the wide public.
The following topics will need to be considered on the way to production:
* better handling of Google Sheets usage quotas, especially for non-free accounts. On my account, I've hit the requests quota very easily and had to apply some artificial delays;
* more requirements clarifications and behavior improvements:
  * in-progress number of the imported products for a task;
  * defining rules for handling duplicates and incomplete data in Google Sheets;
  * defining rules for 'complementing' the importing process (e.g. when user imported 15000 records successfully out of total 27000, and wants to process the remaining 12000 somehow);
* fine-tuning of the settings of all the software packages used &mdash; right now the setups are often just default:
  * database &mdash; indexes, optimizations for particular use cases;
  * Eve &mdash; enabling/disabling bulk operations, configuring filtering, limiting max request rates, etc.;
  * queue manager &mdash; timeouts, handling of failed jobs;
* more load and stress testing (I tested the Google Sheet with 42K records, but it's definitely possible to think of more cases and scenarios).
Still, I believe this project can serve as a solid base for further development.
