## Sonarqube database migration from Oracle to Postgres PoC with Debezium

####  Oracle container registry login
```
docker login container-registry.oracle.com
docker pull container-registry.oracle.com/database/enterprise:latest
```

#### Start Sonarqube 2 times and install Debezium stack
```
docker compose up --build -d
```

#### Create user in PDB for Sonarqube
```
docker compose exec -it oracle_db sqlplus sys/Oracle_123@ORCLPDB1 as sysdba
create user sonar identified by sonar;
grant connect to sonar;
grant all privileges to sonar;
```

```
docker compose restart sonarqube_oracle
```

#### Create admin users in Sonarqube GUI
1. Login as admin/admin http://localhost:8000 and change password to oracle, also add a sonarqube project "oracle" with the GUI.
1. Login as admin/admin http://localhost:9000 and change password to postgres, also add a sonarqube project "postgres" with the GUI.

https://debezium.io/documentation/reference/stable/connectors/oracle.html#_preparing_the_database

#### Create LogMiner directory
```
docker compose exec -it oracle_db sh
mkdir -p /opt/oracle/oradata/recovery_area
```

#### Configure LogMiner and stop database
```
docker compose exec -it oracle_db sqlplus sys/Oracle_123@ORCLCDB as sysdba
alter system set db_recovery_file_dest_size = 10G;
alter system set db_recovery_file_dest = '/opt/oracle/oradata/recovery_area' scope=spfile;
shutdown immediate
```

#### Restart database and edit final configurations
```
docker compose exec -it oracle_db sh
sqlplus / as sysdba
startup mount
alter database archivelog;
alter database open;
-- Should now "Database log mode: Archive Mode"
archive log list

alter database add supplemental log data (primary key, unique) columns;
select SUPPLEMENTAL_LOG_DATA_MIN MIN, SUPPLEMENTAL_LOG_DATA_PK PK, SUPPLEMENTAL_LOG_DATA_UI UI, SUPPLEMENTAL_LOG_DATA_ALL ALL_LOG from v$database;
```

#### Create table spaces for CDC user
https://debezium.io/documentation/reference/stable/connectors/oracle.html#creating-users-for-the-connector
```
docker compose exec -it oracle_db sqlplus sys/Oracle_123@ORCLCDB as sysdba
CREATE TABLESPACE logminer_tbs DATAFILE '/opt/oracle/oradata/ORCLCDB/logminer_tbs.dbf' SIZE 25M REUSE AUTOEXTEND ON MAXSIZE UNLIMITED;
exit;
```
```
docker compose exec -it oracle_db sqlplus sys/Oracle_123@ORCLPDB1 as sysdba
CREATE TABLESPACE logminer_tbs DATAFILE '/opt/oracle/oradata/ORCLCDB/ORCLPDB1/logminer_tbs.dbf' SIZE 25M REUSE AUTOEXTEND ON MAXSIZE UNLIMITED;
exit;
```
#### Create CDC user
```
docker compose exec -it oracle_db sqlplus sys/Oracle_123@ORCLCDB as sysdba

CREATE USER c##sonar IDENTIFIED BY sonar
DEFAULT TABLESPACE logminer_tbs
QUOTA UNLIMITED ON logminer_tbs
CONTAINER=ALL;

GRANT CREATE SESSION TO c##sonar CONTAINER=ALL; 
GRANT SET CONTAINER TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$DATABASE to c##sonar CONTAINER=ALL; 
GRANT FLASHBACK ANY TABLE TO c##sonar CONTAINER=ALL; 
GRANT SELECT ANY TABLE TO c##sonar CONTAINER=ALL; 
GRANT SELECT_CATALOG_ROLE TO c##sonar CONTAINER=ALL; 
GRANT EXECUTE_CATALOG_ROLE TO c##sonar CONTAINER=ALL; 
GRANT SELECT ANY TRANSACTION TO c##sonar CONTAINER=ALL; 
GRANT LOGMINING TO c##sonar CONTAINER=ALL; 

GRANT CREATE TABLE TO c##sonar CONTAINER=ALL; 
GRANT LOCK ANY TABLE TO c##sonar CONTAINER=ALL; 
GRANT CREATE SEQUENCE TO c##sonar CONTAINER=ALL; 

GRANT EXECUTE ON DBMS_LOGMNR TO c##sonar CONTAINER=ALL; 
GRANT EXECUTE ON DBMS_LOGMNR_D TO c##sonar CONTAINER=ALL; 

GRANT SELECT ON V_$LOG TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$LOG_HISTORY TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$LOGMNR_LOGS TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$LOGMNR_CONTENTS TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$LOGMNR_PARAMETERS TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$LOGFILE TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$ARCHIVED_LOG TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$ARCHIVE_DEST_STATUS TO c##sonar CONTAINER=ALL; 
GRANT SELECT ON V_$TRANSACTION TO c##sonar CONTAINER=ALL; 

exit;
```

#### Truncate target Postgres database tables
Truncate all the tables in the Postgres target destination but not the schema_migrations table. This is necessary because during the initial migration the UUID's are generated and are different for each initial migration.
This results in unique key constraint violations because we use the UUID for upserts.
```
select 'truncate table ' || tablename from pg_tables where schemaname = 'public' and tablename != 'schema_migrations';

# Execute the generated SQL commmands
truncate table active_rule_parameters
truncate table active_rules
truncate table alm_pats
truncate table project_alm_settings
truncate table analysis_properties
truncate table app_branch_project_branch
truncate table app_projects
truncate table ce_queue
truncate table ce_activity
truncate table ce_scanner_context
truncate table ce_task_characteristics
truncate table ce_task_input
truncate table ce_task_message
truncate table components
truncate table default_qprofiles
truncate table deprecated_rule_keys
truncate table duplications_index
truncate table es_queue
truncate table event_component_changes
truncate table events
truncate table file_sources
truncate table internal_component_props
truncate table issue_changes
truncate table internal_properties
truncate table issues
truncate table live_measures
truncate table metrics
truncate table new_code_periods
truncate table notifications
truncate table org_qprofiles
truncate table perm_templates_groups
truncate table perm_templates_users
truncate table perm_tpl_characteristics
truncate table permission_templates
truncate table project_branches
truncate table project_links
truncate table project_mappings
truncate table project_measures
truncate table project_qprofiles
truncate table projects
truncate table project_qgates
truncate table plugins
truncate table qprofile_changes
truncate table qprofile_edit_groups
truncate table qprofile_edit_users
truncate table quality_gate_conditions
truncate table session_tokens
truncate table rule_repositories
truncate table rules_parameters
truncate table rules
truncate table rules_profiles
truncate table saml_message_ids
truncate table snapshots
truncate table user_roles
truncate table user_dismissed_messages
truncate table webhook_deliveries
truncate table user_tokens
truncate table webhooks
truncate table groups
truncate table quality_gates
truncate table properties
truncate table group_roles
truncate table groups_users
truncate table users
truncate table audits
truncate table portfolio_projects
truncate table qgate_user_permissions
truncate table qgate_group_permissions
truncate table portfolio_proj_branches
truncate table portfolios
truncate table project_badge_token
truncate table portfolio_references
truncate table new_code_reference_issues
truncate table scanner_analysis_cache
truncate table push_events
truncate table rule_desc_sections
truncate table alm_settings
truncate table scim_users

# duplicate key on admin. not necesarry because of truncate
# update users set login='oldadmin' where login = 'admin'
```

### Debezium deployed with Kafka Connect + Kafka + Kafka Connect Sinks

#### Start Oracle connector
Add output from the following POSTGRES query to boolean.selector in postgres-sink-template.json
```
select string_agg(concat('.*.', upper(column_name)), ',') from information_schema.columns WHERE table_schema <> 'pg_catalog' AND data_type = 'boolean';
```

```
curl -i -X PUT -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/oracle-connector/config -d @register-oracle-logminer.json
```

#### Inspect GUI localhost:3000 for kafka topics and data

#### Add Kafka Postgres JDBC connectors
Auto.create and auto.evolve properties are false because we already have a valid database structure.


#### Add output from the following Postgres query to scripts/generate_sinks.py
```
SELECT concat(tc.table_name, ',', c.column_name)
FROM information_schema.table_constraints tc
JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
AND tc.table_name = c.table_name AND ccu.column_name = c.column_name and tc.table_schema <> 'pg_catalog'
```

#### Generate sinks and execute the sinks. The python script generated the curl statements
```
python generate_sinks.py
    
cd jdbc_sinks
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/active_rule_parameters/config -d @active_rule_parameters.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/active_rules/config -d @active_rules.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/alm_pats/config -d @alm_pats.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/alm_settings/config -d @alm_settings.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_alm_settings/config -d @project_alm_settings.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/analysis_properties/config -d @analysis_properties.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/app_branch_project_branch/config -d @app_branch_project_branch.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/app_projects/config -d @app_projects.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ce_activity/config -d @ce_activity.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ce_queue/config -d @ce_queue.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ce_scanner_context/config -d @ce_scanner_context.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ce_task_characteristics/config -d @ce_task_characteristics.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ce_task_input/config -d @ce_task_input.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ce_task_message/config -d @ce_task_message.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/default_qprofiles/config -d @default_qprofiles.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/deprecated_rule_keys/config -d @deprecated_rule_keys.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/duplications_index/config -d @duplications_index.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/es_queue/config -d @es_queue.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/event_component_changes/config -d @event_component_changes.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/events/config -d @events.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/file_sources/config -d @file_sources.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/group_roles/config -d @group_roles.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/groups/config -d @groups.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/internal_component_props/config -d @internal_component_props.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/internal_properties/config -d @internal_properties.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/issue_changes/config -d @issue_changes.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/issues/config -d @issues.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/live_measures/config -d @live_measures.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/metrics/config -d @metrics.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/new_code_periods/config -d @new_code_periods.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/notifications/config -d @notifications.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/org_qprofiles/config -d @org_qprofiles.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/perm_templates_groups/config -d @perm_templates_groups.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/perm_templates_users/config -d @perm_templates_users.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/perm_tpl_characteristics/config -d @perm_tpl_characteristics.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/permission_templates/config -d @permission_templates.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/plugins/config -d @plugins.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_branches/config -d @project_branches.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_links/config -d @project_links.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_mappings/config -d @project_mappings.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_measures/config -d @project_measures.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_qprofiles/config -d @project_qprofiles.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/projects/config -d @projects.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_qgates/config -d @project_qgates.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/properties/config -d @properties.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/qprofile_changes/config -d @qprofile_changes.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/qprofile_edit_groups/config -d @qprofile_edit_groups.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/qprofile_edit_users/config -d @qprofile_edit_users.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/quality_gate_conditions/config -d @quality_gate_conditions.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/quality_gates/config -d @quality_gates.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/session_tokens/config -d @session_tokens.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/rule_repositories/config -d @rule_repositories.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/rules/config -d @rules.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/rules_parameters/config -d @rules_parameters.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/rules_profiles/config -d @rules_profiles.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/saml_message_ids/config -d @saml_message_ids.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/snapshots/config -d @snapshots.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/user_roles/config -d @user_roles.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/user_dismissed_messages/config -d @user_dismissed_messages.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/user_tokens/config -d @user_tokens.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/users/config -d @users.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/webhook_deliveries/config -d @webhook_deliveries.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/webhooks/config -d @webhooks.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/audits/config -d @audits.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/portfolios/config -d @portfolios.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/portfolio_references/config -d @portfolio_references.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/portfolio_projects/config -d @portfolio_projects.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/qgate_user_permissions/config -d @qgate_user_permissions.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/qgate_group_permissions/config -d @qgate_group_permissions.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/portfolio_proj_branches/config -d @portfolio_proj_branches.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/project_badge_token/config -d @project_badge_token.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/new_code_reference_issues/config -d @new_code_reference_issues.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/scanner_analysis_cache/config -d @scanner_analysis_cache.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/rule_desc_sections/config -d @rule_desc_sections.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/push_events/config -d @push_events.json
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/scim_users/config -d @scim_users.json
```

