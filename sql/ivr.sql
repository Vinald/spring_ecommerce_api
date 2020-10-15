CREATE DATABASE IF NOT EXISTS ivr;

CREATE TABLE IF NOT EXISTS `apps` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `token` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `voice_url` varchar(255) NOT NULL,
  `status_url` varchar(255) NOT NULL,
  `date_created` datetime NOT NULL,
  `date_modified` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`,`token`)
);

CREATE TABLE IF NOT EXISTS `cdr` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(255) NOT NULL,
  `creation_date` datetime NOT NULL,
  `call_start_time` time DEFAULT NULL,
  `call_end_time` time DEFAULT NULL,
  `duration` int(5) NOT NULL DEFAULT 0,
  `token` varchar(255) NOT NULL,
  `peer` varchar(255) NOT NULL,
  `caller_id` varchar(255) NOT NULL,
  `call_id` varchar(255) NOT NULL,
  `external_id` varchar(255) NOT NULL,
  `call_direction` varchar(30) NOT NULL,
  `call_state` varchar(20) DEFAULT NULL,
  `dialed_number` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
);
