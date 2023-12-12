create table sitecounts(
	`site` text,
	`date` date,
	`tags` text
);
create unique index sitecount_site_date on sitecounts(`site`, `date`);

create table sites(
	`dbname` text primary key,
	`url` text,
	`name` text
);
