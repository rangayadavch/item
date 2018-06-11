from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import datetime
from database_setup import *

engine = create_engine('sqlite:///itemcatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()

# Delete Categories if exisitng.
session.query(Category).delete()
# Delete Items if exisitng.
session.query(Items).delete()
# Delete Users if exisitng.
session.query(User).delete()

# Create fake users
User1 = User(name="Ranga",
              email="15pa1a0434@vishnu.edu.in",
              picture='http://dummyimage.com/200x200.png/ff4444/ffffff')
session.add(User1)
session.commit()





# Create fake categories
Category1 = Category(name="Cricket",
                      user_id=1)
session.add(Category1)
session.commit()

Category2 = Category(name="Bikes",
                      user_id=2)
session.add(Category2)
session.commit

Category3 = Category(name="Juice",
                      user_id=1)
session.add(Category3)
session.commit()

Category4 = Category(name="Volley ball",
                      user_id=1)
session.add(Category4)
session.commit()

Category5 = Category(name="Food",
                      user_id=1)
session.add(Category5)
session.commit()

# Populate a category with items for testing
# Using different users for items also
Item1 = Items(name="Helmet",
               date=datetime.datetime.now(),
               description="To save life",
               picture="https://bit.ly/2JJa2o8",
               category_id=1,
               user_id=1)
session.add(Item1)
session.commit()

Item2 = Items(name="Ball",
               date=datetime.datetime.now(),
               description="Shirt to play cricket in.",
               picture="https://bit.ly/2J0JNKi",
               category_id=1,
               user_id=1)
session.add(Item2)
session.commit()

Item3 = Items(name="Bat",
               date=datetime.datetime.now(),
               description="To play cricket",
               picture="https://bit.ly/2MdpNlz",
               category_id=1,
               user_id=1)
session.add(Item3)
session.commit()

print "Your database has been populated with fake data!"