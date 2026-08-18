(() => {
  'use strict';

  const ACCESS_HASH = 'bfdb43ae3a72de447c6a8c3455591aed8a964b5ea256e9148abaf787d39ce64d';
  const STORAGE_KEY = 'erdos193:unlisted-access:v1';
  const CHALLENGE_STORAGE_KEY = `${STORAGE_KEY}:challenge`;
  const WINDOW_GRANT = `${STORAGE_KEY}:${ACCESS_HASH}`;
  const root = document.documentElement;
  const previousVisibility = root.style.visibility;

  root.style.visibility = 'hidden';
  root.dataset.access = 'pending';

  function hasStoredGrant() {
    if (window.name === WINDOW_GRANT) return true;
    try {
      if (localStorage.getItem(STORAGE_KEY) === ACCESS_HASH) return true;
    } catch (_error) {
      // window.name remains as the storage-disabled fallback.
    }
    try {
      return sessionStorage.getItem(STORAGE_KEY) === ACCESS_HASH;
    } catch (_error) {
      return false;
    }
  }

  function storedChallenge() {
    try {
      const challenge = localStorage.getItem(CHALLENGE_STORAGE_KEY);
      if (challenge) return challenge;
    } catch (_error) {}
    try {
      return sessionStorage.getItem(CHALLENGE_STORAGE_KEY);
    } catch (_error) {
      return null;
    }
  }

  function storeGrant(challenge) {
    window.name = WINDOW_GRANT;
    try {
      localStorage.setItem(STORAGE_KEY, ACCESS_HASH);
      localStorage.setItem(CHALLENGE_STORAGE_KEY, challenge);
    } catch (_error) {}
    try {
      sessionStorage.setItem(STORAGE_KEY, ACCESS_HASH);
      sessionStorage.setItem(CHALLENGE_STORAGE_KEY, challenge);
    } catch (_error) {}
  }

  function unlock() {
    delete root.dataset.access;
    root.style.visibility = previousVisibility;
  }

  function deny() {
    location.replace(new URL('404.html', location.href));
  }

  function fragmentState() {
    const fragment = location.hash.slice(1);
    const parameters = new URLSearchParams(fragment);
    return {
      challenge: parameters.get('access'),
      target: parameters.get('target')
    };
  }

  function stripChallengeFragment(target) {
    const targetFragment = target ? `#${encodeURIComponent(target)}` : '';
    history.replaceState(null, '', location.pathname + location.search + targetFragment);
    if (!target) return;
    const scrollToTarget = () => document.getElementById(target)?.scrollIntoView();
    if (document.readyState === 'loading')
      document.addEventListener('DOMContentLoaded', scrollToTarget, {once:true});
    else
      scrollToTarget();
  }

  function keyInternalLinks(challenge) {
    const rewrite = () => {
      for (const anchor of document.querySelectorAll('a[href]')) {
        const raw = anchor.getAttribute('href');
        if (!raw || raw.startsWith('#')) continue;
        const url = new URL(raw, location.href);
        if (url.origin !== location.origin || url.pathname.endsWith('/404.html')) continue;
        if (url.pathname !== '/' && !url.pathname.endsWith('.html')) continue;
        const target = url.hash ? decodeURIComponent(url.hash.slice(1)) : null;
        const parameters = new URLSearchParams();
        parameters.set('access', challenge);
        if (target) parameters.set('target', target);
        url.hash = parameters.toString();
        anchor.href = url.href;
      }
    };
    if (document.readyState === 'loading')
      document.addEventListener('DOMContentLoaded', rewrite, {once:true});
    else
      rewrite();
  }

  async function hash(value) {
    const encoded = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest('SHA-256', encoded);
    return Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
  }

  const fragment = fragmentState();
  if (hasStoredGrant()) {
    const challenge = storedChallenge();
    if (challenge) {
      keyInternalLinks(challenge);
      if (fragment.challenge) stripChallengeFragment(fragment.target);
      unlock();
      window.siteAccessReady = Promise.resolve(true);
      return;
    }
    if (!fragment.challenge) {
      unlock();
      window.siteAccessReady = Promise.resolve(true);
      return;
    }
  }

  if (!fragment.challenge) {
    window.siteAccessReady = Promise.resolve(false);
    deny();
    return;
  }

  window.siteAccessReady = (async () => {
    try {
      if (await hash(fragment.challenge) !== ACCESS_HASH) {
        deny();
        return false;
      }
      storeGrant(fragment.challenge);
      keyInternalLinks(fragment.challenge);
      stripChallengeFragment(fragment.target);
      unlock();
      return true;
    } catch (_error) {
      deny();
      return false;
    }
  })();
})();
