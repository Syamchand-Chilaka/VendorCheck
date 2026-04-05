import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://your-project.supabase.co'
const supabaseAnonKey = 'PASTE_YOUR_ANON_KEY_HERE'

const email = 'PASTE_YOUR_LOGIN_EMAIL_HERE'
const password = 'PASTE_YOUR_PASSWORD_HERE'

const supabase = createClient(supabaseUrl, supabaseAnonKey)

const { data, error } = await supabase.auth.signInWithPassword({
  email,
  password,
})

if (error) {
  console.error('ERROR:', error.message)
  process.exit(1)
}

console.log('ACCESS_TOKEN=' + data.session.access_token)
