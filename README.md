# Calculator telegram bot

This repository contains the code of a telegram bot that provide an inline keyboard calculator.

The bot is configured using the following environment variables:
| **Env Variable** | **Type** | **Description**                                                            |
| :--------------- | :------- | :------------------------------------------------------------------------- |
| `TG_TOKEN`       | `string` | Telegram token from @BotFather (remember not to commit this configuration) |
| `LOG_LEVEL`      | `string` | Logging level                                                              |

# Dependencies

- Python 3.8+
- Pipenv 2021.5.29+q

# Usage

Install dependencies

```sh
pipenv install
```

Run the bot

```sh
pipenv run python -m calculator_bot
```

## Authors

- Ismael Taboada Rodero: [@ismtabo](https://github.com/ismtabo)

