## Minimal cheat sheet

### First setup

```bash
git clone https://github.com/agustinlp5/BBDDtpG10.git
cd BBDDtpG10

./scripts/setup_environment.sh
./scripts/db_rebuild_populate_validate.sh
```

### pgAdmin connection

```text
Host: localhost
Port: 5433
Database: ibd_postgres
User: ibd_postgres
Password: ibd_secretpassword
```

### Start / stop DB

```bash
./scripts/db_up.sh
./scripts/db_down.sh
```

### Rebuild + populate + validate

```bash
./scripts/db_rebuild_populate_validate.sh
```

### Only generate SQL files

```bash
./scripts/generate_sql.sh
```

### Only validate existing DB

```bash
./scripts/db_rebuild_populate_validate.sh --validate-only
```

### Clean local environment

```bash
./scripts/clean_environment.sh
```

### Full reset, including DB data

```bash
./scripts/clean_environment.sh --with-db-volume
```
