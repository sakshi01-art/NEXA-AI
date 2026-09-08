try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    async_playwright = None
    Page = None
    Browser = None
from typing import List, Dict, Optional
import asyncio

class AdvancedWebAutomation:
    """Advanced web automation with Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
    
    async def initialize(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
    
    async def navigate(self, url: str) -> Dict:
        """Navigate to URL"""
        try:
            if not self.page:
                await self.initialize()
            
            await self.page.goto(url)
            
            return {
                'success': True,
                'url': url,
                'title': await self.page.title()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def search_google(self, query: str) -> Dict:
        """Search on Google and return results"""
        try:
            await self.navigate("https://www.google.com")
            
            # Type in search box
            await self.page.fill('textarea[name="q"]', query)
            await self.page.press('textarea[name="q"]', 'Enter')
            
            # Wait for results
            await self.page.wait_for_selector('.g')
            
            # Extract results
            results = await self.page.evaluate('''() => {
                const items = Array.from(document.querySelectorAll('.g'));
                return items.slice(0, 5).map(item => {
                    const title = item.querySelector('h3')?.textContent || '';
                    const link = item.querySelector('a')?.href || '';
                    const snippet = item.querySelector('.VwiC3b')?.textContent || '';
                    return { title, link, snippet };
                });
            }''')
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'count': len(results)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def extract_page_content(self) -> Dict:
        """Extract all content from current page"""
        try:
            content = await self.page.evaluate('''() => {
                return {
                    title: document.title,
                    url: window.location.href,
                    text: document.body.innerText,
                    links: Array.from(document.querySelectorAll('a')).map(a => ({
                        text: a.textContent.trim(),
                        href: a.href
                    })).filter(l => l.text && l.href),
                    images: Array.from(document.querySelectorAll('img')).map(img => ({
                        src: img.src,
                        alt: img.alt
                    }))
                };
            }''')
            
            return {
                'success': True,
                'content': content
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def fill_form(self, form_data: Dict[str, str]) -> Dict:
        """Automatically fill web form"""
        try:
            for selector, value in form_data.items():
                await self.page.fill(selector, value)
            
            return {
                'success': True,
                'message': 'Form filled successfully',
                'fields_filled': len(form_data)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def click_element(self, selector: str) -> Dict:
        """Click element by selector"""
        try:
            await self.page.click(selector)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def take_screenshot(self, path: str = "./temp/screenshot.png") -> Dict:
        """Take screenshot of current page"""
        try:
            await self.page.screenshot(path=path, full_page=True)
            return {
                'success': True,
                'path': path
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def monitor_network(self, duration: int = 10) -> Dict:
        """Monitor network requests"""
        requests = []
        
        async def handle_request(request):
            requests.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type
            })
        
        self.page.on('request', handle_request)
        
        await asyncio.sleep(duration)
        
        self.page.remove_listener('request', handle_request)
        
        return {
            'success': True,
            'requests': requests,
            'count': len(requests)
        }
    
    async def extract_table_data(self, table_selector: str = 'table') -> Dict:
        """Extract data from HTML table"""
        try:
            data = await self.page.evaluate(f'''() => {{
                const table = document.querySelector('{table_selector}');
                if (!table) return null;
                
                const rows = Array.from(table.querySelectorAll('tr'));
                return rows.map(row => {{
                    const cells = Array.from(row.querySelectorAll('td, th'));
                    return cells.map(cell => cell.textContent.trim());
                }});
            }}''')
            
            if data:
                return {
                    'success': True,
                    'data': data,
                    'rows': len(data),
                    'columns': len(data[0]) if data else 0
                }
            
            return {'success': False, 'error': 'Table not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def download_file(self, download_selector: str, save_path: str) -> Dict:
        """Download file from web"""
        try:
            async with self.page.expect_download() as download_info:
                await self.page.click(download_selector)
            
            download = await download_info.value
            await download.save_as(save_path)
            
            return {
                'success': True,
                'path': save_path,
                'filename': download.suggested_filename
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
