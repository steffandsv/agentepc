import asyncio
from dotenv import load_dotenv
from browser_use import Agent, Browser, BrowserProfile, ChatBrowserUse

load_dotenv()

CHROME_PATH = "/home/steff/.cache/ms-playwright/chromium-1200/chrome-linux64/chrome"

async def main():
    profile = BrowserProfile(
        executable_path=CHROME_PATH,
        is_local=True,
        headless=False,     # 👈 JANELA VISÍVEL
        keep_alive=False,
    )

    browser = Browser(browser_profile=profile)
    llm = ChatBrowserUse()

    agent = Agent(
        task="Abra https://sou.mabus.com.br e faça login com: admin e a senha @1516@?Steff. Depois clique no menu superior Deck e clique no menu lateral Licitações Ouro",
        llm=llm,
        browser=browser,
        use_judge=False,
    )

    history = await agent.run()
    print(history.final_result())

if __name__ == "__main__":
    asyncio.run(main())
