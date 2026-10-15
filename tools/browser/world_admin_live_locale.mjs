// Actual installed packages only. No request interception or fabricated API replies.
export function assertLocaleEvidence({sameNode,draft,expectedDraft,callsBefore,callsAfter,readOnlyBefore,readOnlyAfter}){
  if(!sameNode||draft!==expectedDraft||callsBefore!==callsAfter||JSON.stringify(readOnlyBefore)!==JSON.stringify(readOnlyAfter))throw new Error('owned live locale evidence mismatch');
}
export async function qualifyLivePluginLocale({page,expect,root,plugin,nativeSource}){
  if(!['hopae','guard'].includes(plugin))throw new Error('fixed reviewed locale plugin required');
  const calls=[];
  const observer=request=>{const path=new URL(request.url()).pathname;if(path.startsWith(`/v1/plugins/${plugin}/`))calls.push({path,method:request.method()});};
  page.on('request',observer);
  let field,original,handle;
  try{
    if(plugin==='hopae'){
      field=root.locator('textarea');
      await expect(field).toBeVisible();await expect(root.locator('.error')).toHaveText('');
    }else{
      await expect(root.locator('#message')).not.toContainText('연결 중');
      await expect(root.locator('#message')).toHaveAttribute('data-error','false');
      await expect(root.locator('#native-authority-status')).toContainText(nativeSource?'Kubernetes native IP policy source':'local database');
      // Diagnostic draft stays editable while native-owned policy remains locked.
      await root.locator('#tab-kubernetes').click();field=root.locator('#kubernetes-labels');await expect(field).toBeVisible();
    }
    original=await field.inputValue();const draft=plugin==='hopae'?'{ invalid owned-locale draft':'{"owned_locale_draft":"retained"}';
    await field.fill(draft);handle=await field.elementHandle();
    const locks=async()=>plugin==='guard'?Promise.all(['#block-form button[type="submit"]','#allow-save','#policy-form button[type="submit"]','#rules-save','#lua-save','#geoip-reload'].map(s=>root.locator(s).isDisabled())):[];
    const readOnlyBefore=await locks();if(nativeSource)expect(readOnlyBefore.every(Boolean)).toBe(true);
    // Pause the legitimate five-second Sum status poll by hiding its fully
    // mounted panel. Locale changes must still update mounted cached content.
    if(plugin==='guard'){await page.locator('.sidebar [data-view="status"]').click();await expect(root).toBeHidden();}
    const callsBefore=calls.length;
    for(const locale of ['ko','en','ko','en']){
      await page.locator('#locale-select').selectOption(locale);
      if(plugin==='hopae'){
        await expect(root.locator('[data-tab="profiles"]')).toHaveText(locale==='ko'?'인증 프로필':'Authentication profiles');
        await expect(field).toHaveAttribute('aria-label',locale==='ko'?'인증 프로필 설정':'Authentication profile configuration');
        await expect(root.locator('[role="status"]')).toContainText(locale==='ko'?'저장하지 않은 초안':'Unsaved draft');
      }else await expect(root.locator('#native-authority-status')).toContainText(nativeSource?(locale==='ko'?'Kubernetes 네이티브':'Kubernetes native IP policy source'):(locale==='ko'?'로컬 데이터베이스':'local database'));
      await expect(field).toHaveValue(draft);
      // Observe real requests; no route.fulfill/abort/clock replacement.
      await page.waitForTimeout(100);
      assertLocaleEvidence({sameNode:await field.evaluate((node,previous)=>node===previous,handle),draft:await field.inputValue(),expectedDraft:draft,callsBefore,callsAfter:calls.length,readOnlyBefore,readOnlyAfter:await locks()});
    }
    console.log(`PASS: actual installed ${plugin} locale EN/KO preserves draft/DOM, makes no extra owner requests, and retains read-only controls`);
  }finally{
    if(plugin==='guard')await page.locator('.sidebar [data-view="plugin-guard"]').click();
    if(original!==undefined&&field)await field.fill(original);
    if(handle)await handle.dispose();
    if(plugin==='guard')await root.locator('#tab-blocks').click();
    page.off('request',observer);
  }
}
