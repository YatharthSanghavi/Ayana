-- Create profiles table
create table public.profiles (
  id uuid references auth.users on delete cascade not null primary key,
  firstname text,
  lastname text,
  email text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on profiles
alter table public.profiles enable row level security;

create policy "Public profiles are viewable by everyone." on public.profiles
  for select using (true);

create policy "Users can insert their own profile." on public.profiles
  for insert with check (auth.uid() = id);

create policy "Users can update their own profile." on public.profiles
  for update using (auth.uid() = id);

-- Create plan_trips table
create table public.plan_trips (
  id uuid default gen_random_uuid() not null primary key,
  user_id uuid references auth.users on delete cascade not null,
  destination text not null,
  days integer not null,
  budget text,
  travelers text,
  trip_type text,
  interests text,
  markdown text not null,
  budget_data jsonb,
  locations jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on plan_trips
alter table public.plan_trips enable row level security;

create policy "Users can view their own plan trips." on public.plan_trips
  for select using (auth.uid() = user_id);

create policy "Users can insert their own plan trips." on public.plan_trips
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own plan trips." on public.plan_trips
  for update using (auth.uid() = user_id);

create policy "Users can delete their own plan trips." on public.plan_trips
  for delete using (auth.uid() = user_id);

-- Create road_trips table
create table public.road_trips (
  id uuid default gen_random_uuid() not null primary key,
  user_id uuid references auth.users on delete cascade not null,
  start_location text not null,
  end_location text not null,
  start_date text,
  end_date text,
  days integer,
  vehicle text,
  driving_hours text,
  budget text,
  travelers text,
  stops text,
  markdown text not null,
  budget_data jsonb,
  locations jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS on road_trips
alter table public.road_trips enable row level security;

create policy "Users can view their own road trips." on public.road_trips
  for select using (auth.uid() = user_id);

create policy "Users can insert their own road trips." on public.road_trips
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own road trips." on public.road_trips
  for update using (auth.uid() = user_id);

create policy "Users can delete their own road trips." on public.road_trips
  for delete using (auth.uid() = user_id);

-- Trigger function to automatically create a profile entry when a user signs up
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, firstname, lastname, email)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'firstname', ''),
    coalesce(new.raw_user_meta_data->>'lastname', ''),
    new.email
  );
  return new;
end;
$$;

-- Create the trigger
create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
