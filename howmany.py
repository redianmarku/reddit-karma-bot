f=open("posts_replied_to.txt", 'r')
lines = f.read().split(',')
print(len(lines))
